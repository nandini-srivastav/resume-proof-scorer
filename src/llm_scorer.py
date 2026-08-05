"""
The core engine: uses Claude to classify each claimed skill into an
evidence tier and pull a supporting excerpt.

This is the heart of the project — the prompt design, tier definitions,
and stuffing-detection logic are yours to design, not boilerplate.
Only the API call plumbing is scaffolded here.
"""

import anthropic
import json
from src.config import ANTHROPIC_API_KEY
from src.models import SkillEvidence

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def classify_all_skills(jd_skills: list[str], sections: dict) -> list[SkillEvidence]:
  """
  Classify evidence quality for every JD-required skill in a resume.

  This function takes a list of required skills and the resume's segmented sections, 
  and asks Claude to judge each skill's evidence quality - then returns that judgement 
  as structured data that code can use.

  Args:
        jd_skills: List of skills required by the job description.
        sections: Segmented resume sections, as returned by
            segment_sections() (e.g. {"skills": [...], "experience": [...]}).

  Returns:
        A list of SkillEvidence objects, one per skill in jd_skills.

  Raises:
        ValueError: If Claude's response isn't valid, parseable JSON.
  """
  # Step 1 : Build a prompt containing skills to check relevant resume sections.
  prompt = build_prompt(jd_skills, sections)
  response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=2048,
    messages=[{"role": "user", "content": prompt}]
  )
  # extract text content from response
  response_text = response.content[0].text.strip()
  
  # Claude sometimes wraps JSON in a markdown code fence despite instructions
  if response_text.startswith("```"):
    response_text = response_text.strip("`")
    if response_text.startswith("json"):
        response_text = response_text[4:]
    response_text = response_text.strip()
    
  # Step 2 : Parse Calude's response as a JSON.
  try:
    parsed = json.loads(response_text)
  except json.JSONDecodeError as e:
    raise ValueError("Claude returned invalid JSON, could not parse skill evidence") from e
  # Step 3 : if parse succeeds - loop through each skill's result
  evidence_list = []
  for item in parsed:
    # a. Convert it into SkillEvidence object
    evidence_list.append(
      SkillEvidence(
        skill=item["skill"],
        tier=item["tier"],
        excerpt=item["excerpt"],
        github_verified=None,
      )
    )
  # Step 4 : return one SkillEvidence/skill each carrying its tier & supporting excerpt.
  return evidence_list
  

def build_prompt(jd_skills: list[str], sections: dict) -> str:
  """
  Build the prompt sent to Claude for skill evidence classification.

  Includes the tier definitions, the list of skills to classify,
  the relevant resume sections (skills, experience, projects), and
  strict output instructions requiring a JSON-only response.

  Args:
      jd_skills: List of skills required by the job description.
      sections: Segmented resume sections, as returned by
          segment_sections().

  Returns:
      The complete prompt text as a single string.
  """
  
  # skills, experiences and project sectons extracted from the resume (segment_sections())
  skills_text = "\n".join(sections.get("skills", []))
  experience_text = "\n".join(sections.get("experience", []))
  projects_text = "\n".join(sections.get("projects", []))
  
  # The prompt includes:
  # - the three tier definitions
  # - the list of jd_skills to classify
  # - the relevant resume sections (skills, experience, projects)
  # - explicit instruction: respond with ONLY a JSON array, no other text,
  #   one object per skill with fields: skill, tier, excerpt
  prompt = f"""
  You are evaluating a resume to determine whether it provides real evidence for 
  specific claimed skills, not just keyword mentions.
  
  Classify each skill below into one for three tiers:
  Tier 1: The skill appears only in a bare list (e.g., a skills sections) with no 
  supporting context - no project, task, or experience described alongside it.
  
  Tier 2: The skill is mentioned wihin a description of a real project or work 
  experience, with concrete specifics - what was built, what tools or techniques were
  used, and/or what the outcome was.
  
  Tier 3: Same as Tier 2, but the description also references something externally 
  checkable — a named project, repository, or link — that could be independently 
  verified.
  
  Skills to classify: {", ".join(jd_skills)}
  
  SKILLS SECTION:
  {skills_text}
  
  EXPERIENCE SECTION: 
  {experience_text}
  
  PROJECTS SECTION:
  {projects_text}
  
  Respond with ONLY a JSON array, no other text. One object per skill, with this exact 
  structure:
  [{{"skill": "...", "tier": 1, "excerpt": "..."}}]
  """ 
  
  return prompt
 
    
def build_jd_extraction_prompt(jd_text: str) -> str:
  """
  Build the exact prompt sent to Claude to extract skills from a JD.

  Args:
      jd_text (str): Raw job description text.

  Returns:
      str: The complete prompt.
  """
  
  return f"""Extract the technical skills, tools, languages, and frameworks 
required or preferred for this job. Only include specific, checkable skills 
(e.g. "Python", "React", "AWS") — not soft skills (e.g. "communication",
"teamwork") and not vague phrases (e.g. "strong technical background").

Return ONLY a JSON array of strings, nothing else. Example format:
["Python", "React", "PostgreSQL"]
  
Job description:
{jd_text}"""


def extract_skills_from_jd(jd_text: str) -> list[str]:
    """Use Claude to extract required skills from raw job description text.

    Args:
        jd_text (str): Raw job description text pasted by the user.

    Returns:
        list[str]: Extracted skill names. Intended to be shown to the user
            for review/editing before use — extraction can over- or
            under-include skills, this is a starting point, not final.
    """
    
    prompt = build_jd_extraction_prompt(jd_text)

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text
    text = strip_markdown_fences(text)
    skills = json.loads(text)

    return skills
