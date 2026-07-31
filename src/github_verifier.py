"""
Cross-checks claimed skills against a candidate's public GitHub activity.

"""

import requests
import base64
import binascii
from src.config import GITHUB_TOKEN


def fetch_repo_list(username) -> list[dict]:
  """
  Fetch a candidate's public, non-fork repos from GitHub.

  Args:
      username (str): GitHub username to look up.

  Returns:
      list[dict]: Up to 20 repos, sorted by most recently updated,
          forks excluded. Each dict includes at least name, description,
          html_url, fork, updated_at, and owner.

  Raises:
      ValueError: If GitHub returns a non-200 response (bad username,
          rate limited, etc.) — unlike the per-repo fetch functions,
          this one raises because a completely invalid username means
          there's nothing to verify at all, and the caller should know.
  """
  urls = f"https://api.github.com/users/{username}/repos"  # the repo belonging to that username 
  params = {"sort": "updated", "per_page": 100}  # return most-recently-updated first 20 repos, upto 100 results in one call 
  headers = {"Authorization": f"token {GITHUB_TOKEN}"}  # extra metadata, not part of URL, proves who you are to Github
  
  response = requests.get(urls, params=params, headers=headers)
  # if request did not succeed - stop immediately & throw an error
  if response.status_code != 200:
    raise ValueError(f"GitHub API error {response.status_code} for user '{username}': {response.text}")
  
  # Step 1 : parse the JSON response into Python list of dicts, 1 dict/repo
  repos = response.json()
  # Step 2 : drops any repo that's a fork of someone else's project 
  repos = [repo for repo in repos if not repo["fork"]]
  # Step 3 : sorts the repos in descending order - latest to oldest
  repos = sorted(repos, key=lambda repo: repo["updated_at"], reverse=True)
  # Step 4 : Take only first 20 items of the list
  repos = repos[:20]
  
  return repos
  

def fetch_repo_languages(owner: str, repo: str) -> dict:
  """
  _Get the language breakdown for one repo.

  Args:
      owner (str): Repo owner's GitHub username.
      repo (str): Repo name.

  Returns:
      dict: {language_name: byte_count}, e.g. {"Python": 12043, "HTML": 891}.
          Returns {} on any failure — a single repo's languages endpoint
          failing shouldn't break verification for the whole candidate.
  """
  
  urls = f"https://api.github.com/repos/{owner}/{repo}/languages" 
  headers = {"Authorization": f"token {GITHUB_TOKEN}"} 
  
  try:
    response = requests.get(urls, headers=headers)
    # if GitHub responds with an error, return empty dict
    if response.status_code != 200:
      return {}
    return response.json()
  
  # to handle any network related errors
  except requests.exceptions.RequestException:
    return {}

def fetch_readme_text(owner: str, repo: str) -> str:
  """
  Get the plain-text contents of a repo's README, if it has one.

  Args:
      owner (str): Repo owner's GitHub username.
      repo (str): Repo name.

  Returns:
      str: Decoded README text, or "" if the repo has no README (404),
          the request fails, or the content can't be decoded. Never raises.
  """
  urls = f"https://api.github.com/repos/{owner}/{repo}/readme"
  headers = {"Authorization": f"token {GITHUB_TOKEN}"}
  
  try:
    response = requests.get(urls, headers=headers)
    if response.status_code == 404:
      return ""
    if response.status_code != 200:
      return ""
    data = response.json()
    content = base64.b64decode(data["content"])
    return content.decode("utf-8")
  except (requests.exception.RequestException, KeyError, UnicodeDecodeError, binascii.Error):
    return ""
  
def enrich_repo(username) -> str:
  """
  Fetch a candidate's repos plus per-repo languages and README text.

    Args:
        username (str): GitHub username to look up.

    Returns:
        list[dict]: Up to 20 repos, each a dict with name, description,
            languages (dict), and readme (str) attached.

    Raises:
        ValueError: Propagated from fetch_repo_list if the username
            is invalid or the GitHub API request fails.
  """
  # Step 1 : Get candidate's repo - only have metadata, no repo or README content
  repo = fetch_repo_list(username=username)
  
  enriched = []
  # Step 2 : Loop over each repo
  for repo in repos:
    # a. fetch repo languages and README
    owner = repo["owner"]["login"]
    name = repo["name"]
    # b. build a dict per repo(name, description, languages, README)
    enriched.append({
      "name": name,
      "description": repo["description"] or ""
      "language": fetch_repo_languages(owner, name)
      "readme": fetch_readme_text(owner, name)
    })
    
  return enriched
  

def verify_by_language(skill: str, repos: list[dict]) -> tuple[bool, list[str]]:
  """
  This function checks one skill against every repo's language data and 
  collects which repos "prove" it — for example, checking whether the 
  candidate's resume claim of "Python" is backed up by GitHub actually 
  detecting Python in at least one of their repos.

  Args:
        skill (str): Skill to check, e.g. "Python". Matched case-insensitively.
        repos (list[dict]): Enriched repos from enrich_repos().

    Returns:
        tuple[bool, list[str]]: (verified, matching repo names) — verified
            is True if the skill appeared as a language in at least one repo.
  """
  
  # Step 1 : Initialise an empty list to collect proof
  matches = [] 
  # Step 2 : Loop over every repo in enriched list
  for repo in repos:
    # Step 3 : Pull out only the languages detected on Github from the repo
    languages = repo["languages"].key()
    # Step 4 : Checks whether that skill shows up in the list
    if skill.lower() in [lang.lower() for lang in languages]:
      # Step 5 : If matches - add repo name to matches 
      matches.append(repo["name"])
  # Step 6 : Check if did at least one repo matched 
  verified = len(matches) > 0
  return (verified, matches)
  
def verify_by_text(skill: str, repos: list[dict]) -> tuple[bool, list[str]]:
  """
  Same as verify_by_language, but instead of checking a fixed set of language 
  names, it searches free-text (description + README) for the skill, reusing 
  count_occurrences from baseline_scorer.py.

  Args:
      skill (str): Skill to check, e.g. "React". Matched using the same
            word-boundary regex as baseline_scorer.count_occurrences.
      repos (list[dict]): Enriched repos from enrich_repos().

  Returns:
      tuple[bool, list[str]]: (verified, matching repo names) — verified
            is True if the skill appeared in at least one repo's text.
  """
  matches = []
  for repo in repos:
    text = repo["description"] + " " + repo["readme"]
    
    if count_occurences(skill, text) > 0:
      matches.append(repo["name"])
      
  verified = len(matches) > 0
  return (verified, matches)

def build_github_report(skill: str, repos: list[dict]) -> GithubVerification:
  """
  Combine language and text verification into one report for a skill.

  Args:
      skill (str): Skill to verify.
      repos (list[dict]): Enriched repos from enrich_repos().

  Returns:
      GithubVerification: Combined result carrying both signals.
  """
  language_verified, language_evidence = verify_by_language(skill, repos)
  text_verified, text_evidence = verify_by_text(skill, repos)
  
  return GithubVerification(
    skill=skill,
    language_verified=language_verified,
    language_evidence=language_evidence,
    text_verified=text_verified,
    text_evidence=text_evidence,
  )