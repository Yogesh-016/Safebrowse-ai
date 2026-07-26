import os

from dotenv import load_dotenv
from groq import Groq
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse

load_dotenv()  # reads .env file in the project root, if present

# =========================
# CONFIG
# =========================

API_KEY = os.environ.get("GROQ_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY environment variable is not set. "
        "Set it before running, e.g.: export GROQ_API_KEY=your_key_here"
    )

MODEL = "llama-3.3-70b-versatile"

client = Groq(api_key=API_KEY)

# =========================
# WEBSITE SCRAPER
# =========================

def extract_website(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            page = browser.new_page()

            page.goto(url, wait_until="networkidle", timeout=60000)

            text = page.locator("body").inner_text()

            browser.close()

            return text

    except Exception as e:
        return f"ERROR: {e}"


# =========================
# WEBSITE SAFETY CHECK
# =========================

def risk_check(url):

    score = 100
    reasons = []

    parsed = urlparse(url)

    if parsed.scheme != "https":
        score -= 30
        reasons.append("HTTPS not enabled")

    if len(url) > 120:
        score -= 10
        reasons.append("Very long URL")

    suspicious_words = [
        "login",
        "verify",
        "bank",
        "update",
        "secure",
        "account"
    ]

    for word in suspicious_words:
        if word in url.lower():
            score -= 10
            reasons.append(f"Suspicious keyword found: {word}")

    if score >= 80:
        level = "LOW RISK"
    elif score >= 50:
        level = "MEDIUM RISK"
    else:
        level = "HIGH RISK"

    return score, level, reasons


# =========================
# AI SUMMARY
# =========================

def summarize_page(content):

    content = content[:12000]

    prompt = f"""
    Analyze the webpage content.

    Give:
    1. Quick Summary
    2. Key Points
    3. Important Takeaways

    Content:
    {content}
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=700
    )

    return response.choices[0].message.content


# =========================
# CHAT WITH WEBSITE
# =========================

def chat_with_page(page_content):

    print("\n📘 Chat With Website")
    print("Type 'exit' to stop.\n")

    messages = [
        {
            "role": "system",
            "content": f"""
You are an AI assistant.

Answer ONLY using the website content below.

Website Content:
{page_content[:15000]}

If answer is not available,
say:
'I couldn't find that information on this webpage.'
"""
        }
    ]

    while True:

        question = input("You: ")

        if question.lower() == "exit":
            break

        messages.append(
            {
                "role": "user",
                "content": question
            }
        )

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )

        answer = response.choices[0].message.content

        print("\nAI:", answer)
        print()

        messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )


# =========================
# MAIN
# =========================

def main():

    print("=" * 60)
    print("🚀 SafeBrowse AI")
    print("URL Summary + Website Q&A + Risk Detection")
    print("=" * 60)

    url = input("\nEnter URL: ").strip()

    print("\n🔍 Reading website...\n")

    content = extract_website(url)

    if content.startswith("ERROR"):
        print(content)
        return

    print("✅ Website loaded successfully\n")

    print("=" * 60)
    print("🛡 WEBSITE SAFETY REPORT")
    print("=" * 60)

    score, level, reasons = risk_check(url)

    print(f"\nRisk Score : {score}/100")
    print(f"Risk Level : {level}")

    if reasons:
        print("\nFindings:")
        for item in reasons:
            print("•", item)
    else:
        print("\nNo obvious risk indicators found.")

    print("\n" + "=" * 60)
    print("📄 WEBSITE SUMMARY")
    print("=" * 60)

    summary = summarize_page(content)

    print(summary)

    print("\n" + "=" * 60)

    chat_with_page(content)


if __name__ == "__main__":
    main()