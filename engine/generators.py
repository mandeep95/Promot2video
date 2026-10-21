"""
Script generators: prompt -> script JSON for the renderer.

Three modes:
  demo   — no API key needed. Rule-based: detects "Law N" prompts and
           builds the story structure from built-in data; anything else
           gets a generic motivational structure around the topic.
  groq   — free AI. Calls Groq's free tier (llama-3.3-70b) with the
           USER'S OWN key (sent per-request, never stored server-side)
           and validates the JSON it returns.
  paste  — the user pastes their own script/screen text; each paragraph
           becomes a scene.
"""

import json
import re
import urllib.request

VISUALS = ["stall_happy", "stall_idea", "stall_board", "stall_empty",
           "stall_talk", "stall_gradual", "stall_result", "quote", "card",
           "phone_closeup", "split_compare", "growth_chart"]

LAWS = {
    45: {"lines": ["Sab kuch", "ek saath", "mat badlo."],
         "bubble": ["Badlav bura nahi hota,", "tareeka galat hota hai."],
         "moral": "क़ानून पैंतालीस कहता है, बदलाव की बात करो, लेकिन सब कुछ एक साथ मत बदलो। छोटे क़दम, हर रोज़, यही असली तरक़्क़ी है।"},
    1: {"lines": ["Kabhi apne", "aaka se aage", "mat badho."],
        "bubble": ["Chamakna achha hai,", "par sahi jagah par."],
        "moral": "क़ानून एक कहता है, अपने से बड़े को कभी छाया में मत डालो। अपनी चमक ऐसी रखो कि सबको साथ लेकर चले।"},
    3: {"lines": ["Apne iraade", "hamesha", "chhupakar rakho."],
        "bubble": ["Jo dikhta hai,", "wohi sach nahi hota."],
        "moral": "क़ानून तीन कहता है, अपने इरादे छुपाकर रखो। लोग तुम्हारी चाल पहले से जान लेंगे, तो खेल पहले ही ख़त्म हो जाएगा।"},
    6: {"lines": ["Har keemat", "par dhyaan", "aakarshit karo."],
        "bubble": ["Jo dikhega nahi,", "wo bikega nahi."],
        "moral": "क़ानून छह कहता है, हर क़ीमत पर ध्यान आकर्षित करो। भीड़ से अलग दिखना ही पहली सीढ़ी है।"},
    15: {"lines": ["Dushman ko", "poori tarah", "kuchal do."],
         "bubble": ["Aadha kaam,", "poori musibat."],
         "moral": "क़ानून पंद्रह कहता है, जो लड़ाई शुरू करो, उसे पूरी तरह ख़त्म करो। आधा-अधूरा काम बाद में बड़ी मुसीबत बनता है।"},
    28: {"lines": ["Kaam me", "poori", "bebaqi se ghuso."],
         "bubble": ["Darr dikha,", "to khel gaya."],
         "moral": "क़ानून अट्ठाईस कहता है, काम में पूरी बेबाक़ी से घुसो। झिझक कमज़ोरी दिखाती है, हिम्मत रास्ता बनाती है।"},
}


def _law_script(n, law, brand):
    return {
        "title": f"Law {n} — {law['lines'][0]} {law['lines'][1]} "
                 f"{law['lines'][2]}",
        "label": f"LAW {n}",
        "brand": brand,
        "scenes": [
            {"visual": "stall_happy", "headline": "Ek purani dukaan.",
             "narration": "मोहल्ले के कोने पर एक छोटी सी दुकान सालों से चल रही थी। वही पुराना तरीक़ा, वही रोज़ के ग्राहक, सब कुछ आराम से चल रहा था।",
             "pill": [["Wahi purana ", False], ["tareeka", True],
                      [", roz ke graahak.", False]]},
            {"visual": "stall_talk", "headline": "Ek samajhdaar salah.",
             "bubble": law["bubble"],
             "narration": "एक दिन एक समझदार इंसान ने दुकानदार को वो बात कही, जो उसकी ज़िंदगी बदल गई। बात छोटी थी, लेकिन असर बहुत गहरा था।",
             "pill": [["Baat chhoti, ", False], ["asar gehra", True],
                      [".", False]]},
            {"visual": "quote", "lines": law["lines"], "gold": 1,
             "headline": "",
             "narration": law["moral"],
             "pill": [["Yehi hai ", False], [f"Law {n}", True],
                      [" ka saar.", False]]},
            {"visual": "card", "lines": law["lines"], "gold": 1,
             "narration": law["moral"], "pill": []},
        ],
    }


def _generic_script(topic, brand):
    topic = topic.strip()[:60] or "Sapne"
    return {
        "title": topic,
        "label": "DEEP GYAN",
        "brand": brand,
        "scenes": [
            {"visual": "quote", "lines": [topic], "gold": -1, "headline": "",
             "narration": f"आज की बात है, {topic}। ये छोटी सी बात सुनने में आसान लगती है, लेकिन समझने पर ज़िंदगी बदल देती है।",
             "pill": [["Aaj ki baat — ", False], ["khaas", True],
                      [" hai.", False]]},
            {"visual": "stall_happy", "headline": "Ek chhoti si kahani.",
             "narration": "एक छोटे से शहर में एक इंसान रहता था, जो रोज़ थोड़ा-थोड़ा करके आगे बढ़ता था। लोग हँसते थे, पर वो रुकता नहीं था।",
             "pill": [["Roz ", False], ["thoda-thoda", True],
                      [", par roz.", False]]},
            {"visual": "stall_talk", "headline": "Asli baat.",
             "bubble": ["Rukna haar nahi,", "seekhne ka waqt hai."],
             "narration": "समझदार लोग कहते हैं, रुकना हार नहीं होता। रुकना, सीखने और संभलने का वक़्त होता है। असली हार है, कोशिश छोड़ देना।",
             "pill": [["Asli haar — ", False], ["koshish chhodna", True],
                      [".", False]]},
            {"visual": "card",
             "lines": ["Chhote kadam,", "har roz,", "badi manzil."],
             "gold": 1,
             "narration": "याद रखो, छोटे क़दम, हर रोज़, बिना रुके। यही छोटी सी आदत एक दिन बड़ी मंज़िल तक पहुँचाती है।",
             "pill": []},
        ],
    }


def demo_generate(prompt, brand=""):
    m = re.search(r"law\s*(\d{1,2})", prompt, re.I)
    if m and int(m.group(1)) in LAWS:
        n = int(m.group(1))
        return _law_script(n, LAWS[n], brand)
    return _generic_script(prompt, brand)


def paste_generate(text, brand=""):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paras:
        paras = [ln.strip() for ln in text.splitlines() if ln.strip()]
    cycle = ["stall_happy", "stall_idea", "stall_talk", "stall_gradual",
             "stall_result"]
    scenes = []
    for i, para in enumerate(paras[:10]):
        words = para.split()
        headline = " ".join(words[:4]).rstrip("।.,") + "."
        scenes.append({
            "visual": cycle[i % len(cycle)],
            "headline": headline,
            "narration": para,
            "pill": [],
        })
    if len(scenes) >= 2:
        scenes.append({"visual": "card",
                       "lines": ["Chhote kadam,", "har roz,",
                                 "badi manzil."],
                       "gold": 1,
                       "narration": scenes[-1]["narration"],
                       "pill": []})
    return {"title": "My Script", "label": "MY STORY", "brand": brand,
            "scenes": scenes}


SYSTEM = """You write short Hindi story-reels in the BalakheJi flat-animation
style. Return ONLY valid JSON, no markdown, with this exact schema:
{"title": str, "label": str (e.g. "LAW 45"), "brand": "",
 "scenes": [{"visual": one of %s, "headline": str (short Hinglish, Latin,
   max 4 words, ends with .), "narration": str (Hindi in Devanagari script,
   20-30 words, one flowing paragraph), "pill": [[text, is_highlight], ...]
   (one short Hinglish subtitle line, exactly one highlighted segment),
   optional "bubble": [line1, line2] only for stall_talk,
   optional "checklist": [3 short Hinglish items] only for stall_gradual,
   optional "left"/"right": [1-2 short lines] + "left_title"/"right_title"
   only for split_compare,
   optional "bars": [4 short labels] only for growth_chart,
   optional "lines": [3 short lines] and "gold": 1 only for quote/card}]}

Rules: 6-7 scenes. Story arc: setup (stall_happy) -> idea/problem ->
conflict -> advice (stall_talk) -> gradual change (stall_gradual) ->
result (stall_result) -> closing card (card, lines = the moral in 3
lines). Narration must be an original story in your own words, never
copied from any existing video. Language of narration: Hindi Devanagari
only.""" % (VISUALS,)


def groq_generate(prompt, api_key, brand=""):
    body = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Topic: {prompt}"},
        ],
        "temperature": 0.8,
    }).encode()
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions", data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read())
    script = json.loads(data["choices"][0]["message"]["content"])
    # sanitize
    script.setdefault("title", prompt[:60])
    script.setdefault("label", "")
    script["brand"] = brand
    clean = []
    for sc in script.get("scenes", [])[:8]:
        if sc.get("visual") not in VISUALS:
            sc["visual"] = "quote"
        sc.setdefault("headline", "")
        sc.setdefault("narration", "")
        sc.setdefault("pill", [])
        clean.append(sc)
    if not clean:
        raise ValueError("AI returned no scenes")
    script["scenes"] = clean
    return script
