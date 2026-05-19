from groq import Groq
import json
import datetime
import os
from pathlib import Path


JOURNAL_FILE = "journal_history.json"

def load_journal():
    """Load existing journal entries from file."""
    if Path(JOURNAL_FILE).exists():
        with open(JOURNAL_FILE, "r") as f:
            return json.load(f)
    return []

def save_journal(entries):
    """Save journal entries to file."""
    with open(JOURNAL_FILE, "w") as f:
        json.dump(entries, f, indent=2)

def analyze_entry(client, entry_text, past_entries):
    

    history_context = ""
    if past_entries:
        recent = past_entries[-5:]
        history_context = "\n\nPast journal entries for context:\n"
        for e in recent:
            history_context += f"- [{e['date']}] Mood: {e['mood_score']}/10 | {e['summary']}\n"

    prompt = f"""You are an empathetic AI therapist and mood analyst. Analyze this journal entry deeply.

Journal Entry:
"{entry_text}"
{history_context}

Respond ONLY with a valid JSON object (no markdown, no explanation) in this exact format:
{{
  "mood_score": <integer 1-10, where 1=very negative, 10=very positive>,
  "primary_emotion": "<single dominant emotion like: Joy, Sadness, Anxiety, Anger, Hope, Frustration, Contentment, Fear, Excitement, Grief>",
  "secondary_emotions": ["<emotion1>", "<emotion2>"],
  "summary": "<one sentence summary of the entry's emotional core>",
  "insights": ["<insight1>", "<insight2>", "<insight3>"],
  "affirmation": "<one warm, personalized affirmation based on their entry>",
  "suggestion": "<one specific, actionable suggestion to improve their mood or situation>",
  "pattern_note": "<if past entries exist, note any emotional trend; otherwise say 'First entry - baseline established'>",
  "keywords": ["<emotional_keyword1>", "<emotional_keyword2>", "<emotional_keyword3>"]
}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.choices[0].message.content.strip()

    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def display_analysis(analysis, date_str):
    """Pretty print the mood analysis."""
    mood = analysis['mood_score']
    

    filled = "█" * mood
    empty = "░" * (10 - mood)
    mood_bar = f"[{filled}{empty}] {mood}/10"
    

    if mood >= 7:
        mood_status = "Positive"
    elif mood >= 4:
        mood_status = "Neutral"
    else:
        mood_status = "Difficult"

    print("\n" + "═" * 60)
    print(f"  MOOD ANALYSIS — {date_str}")
    print("═" * 60)
    
    print(f"\n  Mood Score:  {mood_bar}")
    print(f"  Status:      {mood_status}")
    print(f"  Primary:     {analysis['primary_emotion']}")
    print(f"  Secondary:   {', '.join(analysis['secondary_emotions'])}")
    print(f"  Keywords:    {', '.join(analysis['keywords'])}")
    
    print(f"\n  Summary")
    print(f"  {analysis['summary']}")
    
    print(f"\n  Insights")
    for i, insight in enumerate(analysis['insights'], 1):
        print(f"  {i}. {insight}")
    
    print(f"\n  Affirmation")
    print(f"  \"{analysis['affirmation']}\"")
    
    print(f"\n  Suggestion")
    print(f"  {analysis['suggestion']}")
    
    print(f"\n  Pattern Note")
    print(f"  {analysis['pattern_note']}")
    
    print("\n" + "═" * 60)

def show_mood_history(entries):
    """Show a simple mood trend chart from past entries."""
    if not entries:
        print("\n  No previous entries found.")
        return
    
    print("\n" + "═" * 60)
    print("  MOOD HISTORY")
    print("═" * 60)
    
    recent = entries[-10:]
    for entry in recent:
        score = entry['mood_score']
        bar = "█" * score + "░" * (10 - score)
        emotion = entry['primary_emotion'][:12].ljust(12)
        print(f"  {entry['date']}  [{bar}] {score:2d}  {emotion}  {entry['summary'][:35]}...")
    

    avg = sum(e['mood_score'] for e in recent) / len(recent)
    print(f"\n  Average Mood: {avg:.1f}/10")
    print("═" * 60)

def main():
    print("\n" + "═" * 60)
    print("  AI MOOD JOURNAL  — project by sshw.")
    print("  Your personal emotional intelligence companion")
    print("═" * 60)
    

    api_key = "[YOUR_API_KEY]"
    if not api_key:
        print("\n  ERROR: Set GROQ_API_KEY environment variable")
        return
    
    client = Groq(api_key=api_key)
    journal = load_journal()
    
    print("\n  Commands:")
    print("  [1] Write a new journal entry")
    print("  [2] View mood history")
    print("  [3] Exit")
    
    while True:
        print()
        choice = input("  Choose (1/2/3): ").strip()
        
        if choice == "3":
            print("\n  Take care of yourself. See you next time!\n")
            break
            
        elif choice == "2":
            show_mood_history(journal)
            
        elif choice == "1":
            print("\n  Write your journal entry (press Enter twice when done):")
            print("  " + "-" * 56)
            
            lines = []
            while True:
                line = input("  ")
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)
            
            entry_text = "\n".join(lines).strip()
            
            if len(entry_text) < 10:
                print("\n  WARNING: Entry too short. Please write more.")
                continue
            
            print("\n  Analyzing your entry with AI...")
            
            try:
                date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                analysis = analyze_entry(client, entry_text, journal)
                
                # Save entry
                entry_record = {
                    "date": date_str,
                    "entry": entry_text,
                    "mood_score": analysis["mood_score"],
                    "primary_emotion": analysis["primary_emotion"],
                    "summary": analysis["summary"],
                    "full_analysis": analysis
                }
                journal.append(entry_record)
                save_journal(journal)
                
                display_analysis(analysis, date_str)
                print(f"\n  Entry saved to {JOURNAL_FILE}")
                
            except json.JSONDecodeError as e:
                print(f"\n  ERROR: Failed to parse AI response: {e}")
            except Exception as e:
                print(f"\n  ERROR: API Error: {e}")
        else:
            print("  Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
