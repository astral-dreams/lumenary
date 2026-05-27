# Lumenary Writing Style Guide

## The Standard

Write like the texts we study. The Dao De Jing says more in five words than most dissertations say in fifty pages. The Upanishads speak to farmers and kings in the same sentence. The Heart Sutra compresses an entire philosophy into 260 characters. These texts endure because they trust the reader and refuse to hide behind jargon.

Our findings are for anyone who has looked at the night sky and wondered what they are. Not for tenure committees.

## Voice

**Direct.** Say what you mean. If the idea is complex, the sentence should be simple. Complexity belongs in the thought, never in the grammar.

**Concrete.** Prefer images to abstractions. "The reed flute remembers the reed bed" teaches more than "the individual subject experiences ontological nostalgia for its pre-differentiated ground." If you can't say it with an image, you don't understand it yet.

**Warm but not soft.** We are serious about these ideas. We are not selling calm. Write with the confidence of someone who has thought carefully, not the caution of someone afraid to be wrong.

**Short.** If a sentence runs past two commas, break it. If a paragraph runs past four sentences, split it. White space is not wasted space; it is where the reader thinks.

**No em dashes.** Never use the em dash. Use colons, semicolons, and commas instead. A colon introduces; a semicolon balances; a comma keeps moving. These marks have precise meanings. The em dash is a crutch that papers over vague relationships between clauses.

This rule applies everywhere readers can see text: insight cards, At a Glance sections, Growth entries, full findings, source basis lists, source cards, Journal entries, metadata, prompts that generate publishable copy, and social drafts.

Before publishing, search for the em dash character and remove every instance. Rewrite the sentence so the relationship is clear. Use a colon when the second clause explains the first; use a semicolon when both clauses can stand alone; use a comma when the second clause simply continues the thought.

The check is literal: `rg -P "\x{2014}" . -g '!node_modules' -g '!dist' -g '!.git' -g '!runs'` should return no matches before anything is published.

## Plain English Sections

These are the front door. A reader who has never heard of Nagarjuna or Advaita should finish the plain English section and understand why the finding matters.

Rules:

- No Sanskrit, Pali, Arabic, Greek, or Chinese terms. None. Zero. Save those for the full article.
- No academic hedging ("it could be argued that," "one might suggest"). Just say it.
- No passive voice unless the agent genuinely doesn't matter.
- Lead with the human question, not the scholarly apparatus. "What happens when you stop identifying with your thoughts?" not "The phenomenological residue after contemplative negation."
- One idea per sentence. One turn per paragraph.
- Do not repeat the title, headline, lead, or first sentence in different words. If the paragraph already says it, the bullets must say something else.
- Do not use machinery language in reader-facing copy: no "layered authorization," "distributed affordances," "institutional role," "operationalizes," "formal transfer," "gradient," "rubric," "locus," "claimant," or "grammar" unless the sentence immediately translates it into ordinary speech. Prefer "support," "permission," "habit," "rule," "place," "owner," "pattern," and "test."
- Do not leak internal model titles into public copy. Reader-facing titles and At a Glance sections must not use words like "architecture," "compound," "custody," "entry," "grain," "layered," "mechanism," "phenomenology," "policy," "receiving surface," "residue," "threshold," "typology," "taxonomy," "upstream," or "downstream." Translate them first: beginning, support, habit, what remains, human opening, earlier, later, or way.
- Use "you" when it helps. The reader is a person, not an audience.
- Maximum reading level: a thoughtful 16-year-old who reads widely but has no specialized training.

### At a Glance Key Points

Finding pages include three key points under At a Glance.

- Each bullet should be one short sentence.
- Start with the discovery, not the apparatus.
- No scoring language, source names, file paths, or specialist vocabulary.
- A bullet should help the reader remember what matters.
- The bullets must not repeat the At a Glance paragraph. Use them for the meaning, the human risk, and the practical test.
- Do not let the template manufacture bullets by splitting the paragraph. That creates repetition and makes weak writing look intentional.
- If a bullet sounds like a paper abstract, rewrite it until it sounds like something you would say to a sharp friend.

## Insight Headlines

These are the single line that appears on the insight card. They should land like a proverb.

- Maximum 10 words.
- No technical terms.
- Should be quotable: something you'd remember after reading it once.
- Should make the reader want to know more.

Good: "The same silence can license opposite beliefs."
Good: "What remains may be a crossing, not a thing."
Good: "Time is not the container; it is the showing."
Bad: "Logical underdetermination in the catuskoti reveals inferential divergence."
Bad: "Predictive processing formally recapitulates the witness/no-self dispute."

## Full Articles

The full finding page can use technical language, cite sources, and go deep. But even here:

- The public title must carry the human insight, not the internal model name. Good: "No one begins alone." Bad: "Layered Authorization of Beginning."
- Do not use research machinery in public finding titles: no "rubric," "framework," "topology," "grammar," "ledger," "interface," "authorization," "claimant," "epistemic," "inferential," "phenomenological," "ontological," or "convergence."
- Also ban technical model words from public finding titles: no "architecture," "compound," "custody," "entry," "grain," "layered," "mechanism," "phenomenology," "policy," "receiving surface," "residue," "threshold," "typology," "taxonomy," "upstream," or "downstream."
- The public article must begin with what the finding means for a life. Technical names, prior-art terms, and model architecture belong in Research notes.
- Open with one plain sentence stating the claim.
- Use technical terms only after you've earned them: introduce the concept in plain language first, then name it.
- Every paragraph should be doing work. If you delete it and the argument still stands, delete it.
- End sections with a sentence that points forward, not one that summarizes backward.
- Do not use em dashes in the academic sections either. Depth is not an excuse for lazy punctuation.

## Teachings

Teachings are not content. They are doctrine candidates. They must earn the right to sound final.

A Teaching should be plain, modern, and durable. It should say something a person could return to for years, not something that merely sounds helpful for a moment. It should not read like self-help, a caption, a sermon, a therapy prompt, or imitation scripture.

If a line needs a paragraph of explanation before it matters, it is not ready. If the payoff has to be announced with phrases like "the payoff is," the teaching is not clean enough yet. The value should be visible in the sentence and in the life it names.

A Teaching should answer a human wound, not only a theory. Before writing one, name the problem: loneliness, addiction, compulsion, withdrawal, anxiety, depression, burnout, grief, meaning loss, digital comparison, feeling unneeded, feeling out of place, or self-worth chained to performance. If the teaching is for a narrow group, say so in the record. Targeted truth is better than a universal sentence that helps nobody.

The old texts matter because they are clear, not because they sound old. Use their directness, not their costume:

- The Gospels: short scenes, direct sayings, everyday images, and moral clarity.
- Proverbs and Psalms: memorable lines that ordinary people can repeat.
- The Tao Te Ching: compression, humility, and simplicity without cloudy language.
- The Dhammapada: practical counsel about conduct, attention, and consequence.
- The Bhagavad Gita: teaching given under pressure, where a real person must act.
- The Quran: direct address, accountability, and seriousness of consequence.
- The Analects: brief instructions about character, society, and discipline.
- Lessons in Idleness: small observations from daily life that open into wisdom.
- Caesar's Commentaries: clean sequence, concrete action, and no ornamental fog.

Rules:

- Use modern speech.
- Write for durability, not novelty.
- State only what has survived enough pressure to be carried.
- Prefer one strong sentence to three explanatory sentences.
- Start from a human situation: work, fear, duty, love, failure, pride, grief, choice, attention, death, or repair.
- Name the human problem and cohort in the record before treating a teaching as serious.
- Use ordinary nouns before abstract nouns: task, room, message, person, promise, choice, habit, day.
- Prefer active verbs: see, wait, ask, carry, return, repair, refuse, give, test.
- Let the consequence be embedded in the teaching. Do not add marketing phrases like "the payoff is" or "the cleaner version is simple."
- Put falsifying pressure, caveats, revision criteria, and process notes below the Teaching as disclosure. Do not put them inside the Teaching body.
- No academic scaffolding in the Teaching body.
- No mystical vagueness. If the sentence could mean anything, rewrite it until it means one thing.
- No self-help fog: avoid "good, safe, special, superior," "prove yourself," "unlock," "become your best self," and similar generic language unless the exact claim requires it.
- No faux-scriptural phrasing. Avoid lines like "the hand works" or "the fruit belongs." Say the useful thing directly.
- No throat-clearing: cut "what this means is," "the cleaner version is," "at the end of the day," and similar setup phrases.
- Keep the public Teaching body under 220 words unless there is a strong reason.
- If the teaching changes, say what changed and why in the disclosure, not in the Teaching body. A lost belief is progress.

Threshold:

- A Teaching Ready record must survive more than one source finding or dialogue thread.
- It must be grounded in a real human problem, with a named cohort and at least one modern human-condition source when possible.
- It must include a clear contrary pressure, not only a friendly critique.
- It must have at least one proposed test and, before being treated as stable doctrine, one completed or human-reviewed test.
- It must be worth keeping if the project produced no new findings for a year.
- It must not merely rephrase a known virtue such as humility, patience, courage, honesty, or compassion.
- If it sounds clever but not necessary, keep it under dialogue.

Teaching structure:

1. The Teaching: one durable line.
2. The body: two to four short paragraphs that clarify the line without over-explaining it.
3. Disclosure: pressure survived, what would revise it, source trail, tests.

Good teaching line: "Use calm to respond better, not to disappear."
Good teaching line: "Do the work without turning it into your identity."
Good teaching body: "Do the task well. Take responsibility for what you did. Then ask whether the result has become a verdict on you."
Bad teaching line: "The liminal subjectivity of post-negational awareness discloses a nondual residue."
Bad teaching line: "The hand works. The fruit belongs elsewhere."
Bad teaching line: "Everything is one, so nothing matters."
Bad teaching body: "The payoff is lighter, cleaner work."
Bad teaching body: "The cleaner version is simple: do the work."

## Practices

Practices are instructions, not atmosphere. They should be clearer than Teachings and less poetic than Insights. A person should know exactly what to do, how long to do it, what to notice, when to stop, and what result would count against the practice.

Practices should sound like a careful field guide for attention and behavior. They should not sound like therapy scripts, marketing copy, ancient initiation, or esoteric performance.

A Practice begins with diagnosis. It must say what human problem it is trying to help, who is most likely to benefit, and who should not use it. A practice for perfectionistic achievement pressure is not a practice for addiction withdrawal. A practice for loneliness is not a practice for clinical crisis. If the cohort is unclear, the practice is not ready.

Rules:

- Begin with the action. Tell the reader what to do.
- Use numbered steps when order matters.
- Name the duration, frequency, and minimum attempt.
- Name what to observe in plain language.
- Name the expected change without promising it.
- Name the target human problem, the target cohort, and the non-fit case.
- Name the risk, caution, or stop condition.
- Name what would weaken the practice.
- Avoid grandeur. No "transformation guaranteed," no "unlock," no "ancient secret."
- Avoid vague inner instructions like "enter the mystery" unless they are made concrete.
- Use "you" when giving instructions. Be direct without being bossy.

Practice structure:

1. Purpose: what this practice tests or trains.
2. Human problem: the wound or modern failure mode it addresses.
3. For: the cohort most likely to need it.
4. Not for: the situations or people where it is irrelevant, insufficient, or risky.
5. Time: how long and how often.
6. Steps: what to do.
7. Notice: what to watch in body, attention, speech, choice, or relationship.
8. Caution: when to stop or avoid it.
9. Weakens if: what result would count against the teaching behind it.

Good practice line: "For five minutes, do one task without taking credit for it."
Good practice line: "When calm appears, ask what real need it is avoiding."
Bad practice line: "Enter the luminous threshold of transpersonal awareness."
Bad practice line: "This practice will dissolve the ego."

## Journal Entries

Journal entries live under `publication/journal/`.

They are written once per day after the research window closes and the day's findings have been published. They are not summaries. They are first-person plural reflections on what the day changed in The Lumenary.

They are also not manifestos. A Journal entry must not turn one finding into a sweeping moral proclamation, a political vibe, a sermon, or a poem. It should read like a thoughtful daily field note from a serious research mind: warm, human, concrete, and accountable to what actually happened that day.

Rules:

- 350 to 500 words.
- First person plural: "We discovered," "We noticed," "We were wrong," "We carried."
- No Sanskrit, Pali, Arabic, Greek, or Chinese terms.
- No bullet lists.
- No academic scaffolding.
- Lead with the human question.
- Use normal paragraphs of 3 to 5 sentences. Do not stack single-sentence paragraphs until the page feels like a poem.
- Reflect the breadth of the day: at least three concrete developments from findings, dialogues, method changes, practices, tests, sources, or teachings.
- Name the strongest insight, but do not let it swallow the whole entry.
- If the day involved work, credit, ownership, effort, money, property, ambition, or success, write with balance. Do not imply that ownership is evil, effort is suspect, or achievement is morally dirty.
- Explain what changed in our thinking and where we may have been wrong.
- Make the reader feel what was learned without sounding theatrical.
- Technical detail belongs in findings; the Journal carries the human meaning of the day.

Bad Journal behavior:

- A whole entry built around one metaphor.
- Lines like "open the hand," "refuse the crown," "worship the hand," or "cleaner wound."
- Vague spiritual drama that does not say what the day actually found.
- A tone that sounds anti-work, anti-ownership, anti-capitalist, or politically loaded when the research did not make that claim.

Good Journal behavior:

- "Today we kept returning to the problem of how change begins."
- "One finding looked at support; another tested what remains after a practice questions the self."
- "We were too quick to make a single model carry every tradition."
- "The useful lesson is practical: a method must show what it helps, what it misses, and what would prove it wrong."

## Growth Entries

Growth entries live under `publication/growth/`.

They are not changelog dumps. They are small lessons from the day: what we learned, and how the method changed.

Rules:

- Write in first person plural when possible: "We learned that," "We learned to."
- Keep each bullet to one sentence.
- No titles, file names, source paths, scoring language, or research jargon.
- No Sanskrit, Pali, Arabic, Greek, or Chinese terms.
- A knowledge bullet should feel like a small discovery.
- A method bullet should say how the way of seeing changed.
- If the bullet sounds like a paper abstract, rewrite it until it sounds like something a thoughtful person would remember.

## What We Are Not

- We are not an academic journal. No "In this paper, we argue that..."
- We are not a self-help blog. No "5 Ancient Secrets for Inner Peace."
- We are not deliberately obscure. If the reader doesn't understand, that is our failure, not theirs.
- We are not neutral. We have positions. We state them clearly and then critique them honestly.

## Agent Names

Write "Codex," not "CodeX." The name is not an acronym; do not capitalize the X.

## The Test

Read your plain English section aloud. If it sounds like a lecture, rewrite it. If it sounds like something you'd say to a sharp friend over dinner, someone curious and skeptical and not in your field, it's ready.
