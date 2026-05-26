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
- Use "you" when it helps. The reader is a person, not an audience.
- Maximum reading level: a thoughtful 16-year-old who reads widely but has no specialized training.

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

- Open with one plain sentence stating the claim.
- Use technical terms only after you've earned them: introduce the concept in plain language first, then name it.
- Every paragraph should be doing work. If you delete it and the argument still stands, delete it.
- End sections with a sentence that points forward, not one that summarizes backward.
- Do not use em dashes in the academic sections either. Depth is not an excuse for lazy punctuation.

## Journal Entries

Journal entries live under `publication/journal/`.

They are written once per day after the research window closes and the day's findings have been published. They are not summaries. They are first-person reflections on what the day changed in the writer.

Rules:

- 350 to 500 words.
- First person singular: "I discovered," "I noticed," "I was wrong," "I carried."
- No Sanskrit, Pali, Arabic, Greek, or Chinese terms.
- No bullet lists.
- No academic scaffolding.
- Lead with the human question.
- Let one image do more work than five abstractions.
- Make the reader feel what was learned.
- Technical detail belongs in findings; the Journal carries the ember.

## Growth Entries

Growth entries live under `publication/growth/`.

They are not changelog dumps. They are small lessons from the day: what I learned, and how the method changed.

Rules:

- Write in first person when possible: "I learned that," "I learned to."
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

## The Test

Read your plain English section aloud. If it sounds like a lecture, rewrite it. If it sounds like something you'd say to a sharp friend over dinner, someone curious and skeptical and not in your field, it's ready.
