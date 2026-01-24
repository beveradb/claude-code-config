---
description: Create high-quality SEO content through collaborative interview process
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, WebFetch, WebSearch, AskUserQuestion, mcp__gsc-server__*, mcp__google-analytics__*
---

# SEO Content Creation

Create genuinely valuable, personalized content for your website through a collaborative interview process. This skill helps you produce content that reflects your actual knowledge and expertise rather than generic AI-generated text.

## Arguments

- `$ARGUMENTS` - Topic, page idea, or "discover" to identify content opportunities

## Philosophy

**Why this matters for SEO:**
- Google rewards helpful, original content written by people with genuine expertise
- Thin, generic content hurts rankings; depth and uniqueness help
- Multiple focused pages targeting specific topics outperform one bloated homepage
- E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness) is a ranking factor

**This skill's approach:**
1. Identify what content would genuinely help your audience
2. Create a structure that serves both users and search engines
3. Interview you to extract YOUR knowledge, experiences, and opinions
4. Produce content that sounds like you, not like AI

## Instructions

### Phase 1: Content Discovery (if no specific topic provided)

If the user says "discover" or doesn't specify a topic, analyze their site for content opportunities.

#### 1a. Analyze Current Content Gap

Review GSC data for queries where you rank but don't have dedicated pages:
```
mcp__gsc-server__get_advanced_search_analytics(
  site_url="...",
  dimensions="query",
  sort_by="impressions",
  sort_direction="descending",
  row_limit=100
)
```

Look for:
- High-impression queries that don't have dedicated landing pages
- Question-based queries (how, what, why, when, where)
- Long-tail queries that could be individual articles
- Related topics your audience searches for

#### 1b. Analyze Competitor Content (Optional)

If the user provides competitor URLs, research what topics they cover that you don't.

#### 1c. Present Content Opportunities

Present a prioritized list of content ideas:

```
## Content Opportunities for [site]

Based on your search data, here are pages that could improve your SEO:

### High Priority (High search volume, you're already ranking)
1. **[Topic]** - You rank #X for "[query]" (X impressions/month)
   - Current situation: [no dedicated page / buried in homepage]
   - Opportunity: Dedicated page could capture more traffic

2. ...

### Medium Priority (Related topics your audience searches)
1. **[Topic]** - Related to your core offering
   - Search intent: [informational/transactional]
   - Why it fits: [explanation]

### Content Structure Suggestions
- Consider breaking your homepage into:
  - /[topic-1] - Dedicated page for [topic]
  - /[topic-2] - Dedicated page for [topic]
  - /blog/[article] - Educational content

Which topic would you like to create content for?
```

### Phase 2: Content Planning

Once a topic is chosen, plan the content structure.

#### 2a. Research Search Intent

Understand what people searching for this topic actually want:
```
mcp__gsc-server__get_advanced_search_analytics(
  site_url="...",
  dimensions="query",
  filter_dimension="query",
  filter_operator="contains",
  filter_expression="[topic keywords]",
  row_limit=50
)
```

Also use WebSearch to see what currently ranks:
```
WebSearch for "[main keyword]" to understand the competitive landscape
```

#### 2b. Propose Content Structure

Present a proposed structure for user approval:

```
## Proposed Structure: [Page Title]

**Target Keywords:**
- Primary: [main keyword]
- Secondary: [related keywords from research]

**Search Intent:** [informational / transactional / navigational]

**Proposed Sections:**
1. **[Section 1]** - [What this covers and why]
2. **[Section 2]** - [What this covers and why]
3. **[Section 3]** - [What this covers and why]
4. **FAQ Section** - Address common questions
5. **Call to Action** - [What action should readers take]

**Estimated Length:** ~[X] words (based on competitor analysis)

Does this structure work? Any sections to add/remove/modify?
```

### Phase 3: The Interview Process

This is the critical phase that makes content genuinely yours.

#### 3a. Section-by-Section Interview

For EACH section, conduct a mini-interview using AskUserQuestion:

```
## Let's build Section 1: [Section Title]

I'll ask you a few questions to capture your actual knowledge and perspective.
```

**Question types to ask:**

1. **Experience questions:**
   - "What's your personal experience with [topic]?"
   - "What mistakes have you seen people make with [topic]?"
   - "What's something most people get wrong about [topic]?"

2. **Expertise questions:**
   - "What would you tell a friend who asked about [topic]?"
   - "What's the most important thing to understand about [topic]?"
   - "Are there any nuances or 'it depends' factors?"

3. **Opinion questions:**
   - "What's your take on [common debate in the field]?"
   - "What approach do you recommend and why?"
   - "What would you do differently than the standard advice?"

4. **Specificity questions:**
   - "Can you give a specific example?"
   - "What numbers or data points are relevant here?"
   - "Who specifically is this advice for?"

Use AskUserQuestion with focused options + "Other" for open responses:

```
AskUserQuestion(
  questions=[{
    "question": "What's the biggest misconception people have about [topic]?",
    "header": "Misconceptions",
    "options": [
      {"label": "[Common misconception 1]", "description": "Many people think..."},
      {"label": "[Common misconception 2]", "description": "Another common belief..."},
      {"label": "Something else", "description": "Share your own observation"}
    ],
    "multiSelect": false
  }]
)
```

#### 3b. Capture Voice and Tone

Ask about communication preferences:

```
AskUserQuestion(
  questions=[{
    "question": "How do you want to come across in this content?",
    "header": "Tone",
    "options": [
      {"label": "Professional expert", "description": "Authoritative, data-driven, formal"},
      {"label": "Friendly guide", "description": "Approachable, conversational, supportive"},
      {"label": "Straight-talking peer", "description": "Direct, no-nonsense, practical"},
      {"label": "Enthusiastic educator", "description": "Passionate, detailed, thorough"}
    ],
    "multiSelect": false
  }]
)
```

#### 3c. Gather Unique Angles

Ask what makes their perspective different:

- "What do you know about [topic] that most articles don't cover?"
- "What would you add to the typical advice on this?"
- "What's your unique angle or approach?"

### Phase 4: Content Generation

#### 4a. Generate Draft with User's Input

Write the content incorporating:
- Their actual words and phrases where possible
- Specific examples they provided
- Their opinions and recommendations
- Their preferred tone and style

**Structure the content for SEO:**
- Clear H1 with primary keyword
- Logical H2/H3 hierarchy
- Short paragraphs (2-4 sentences)
- Bullet points for scannable information
- FAQ section with schema-ready Q&A format

#### 4b. Review and Refine

Present the draft section by section, asking:
- "Does this accurately reflect your view?"
- "Anything to add, change, or remove?"
- "Does this sound like you?"

Make revisions based on feedback.

#### 4c. AI Pattern Review

**CRITICAL:** Before finalizing, review the content against known AI writing patterns. The goal is content that reflects genuine human expertise, not text that screams "AI wrote this."

Reference: [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)

**Check for and fix these patterns:**

##### Language Red Flags

| Pattern | Problem | Fix |
|---------|---------|-----|
| **Rule of three overuse** | AI loves triads: "convenient, efficient, and innovative" | Let content determine structure. Sometimes 2 items, sometimes 4. |
| **Em dash overuse** | AI uses — where humans use commas, colons, or parentheses | Replace most em dashes with simpler punctuation |
| **Trailing importance claims** | "emphasizing the significance of...", "reflecting the continued relevance of...", "underscoring the importance of..." | Delete these. If it's important, show don't tell. |
| **Servile positivity** | Everything described in glowing, generic terms | Add specific critiques, nuances, trade-offs |
| **Overly formal register** | Unnecessarily stiff or elevated language | Use conversational language the user actually uses |

##### Structural Red Flags

| Pattern | Problem | Fix |
|---------|---------|-----|
| **Uniform sentence length** | Every sentence ~15-20 words | Vary drastically: some 5 words, some 30 |
| **Parallel structure everywhere** | Every paragraph follows same pattern | Break patterns intentionally |
| **Excessive bullet lists** | Everything bulleted for "scannability" | Use prose. Lists only when truly listing items. |
| **Intro-body-conclusion formula** | Robotic "In this article... Finally..." | Start with a hook. End when done. |

##### Word/Phrase Red Flags

Avoid or minimize these AI-favorite words and phrases:

**Overused intensifiers:**
- "delve into", "dive deep", "unpack"
- "crucial", "vital", "essential", "pivotal"
- "robust", "comprehensive", "holistic"
- "leverage", "utilize" (just say "use")
- "realm", "landscape", "sphere"
- "plethora", "myriad", "multifaceted"
- "seamlessly", "effortlessly"
- "cutting-edge", "groundbreaking", "revolutionary"

**Hollow connectors:**
- "It's worth noting that..."
- "It's important to understand that..."
- "When it comes to..."
- "In today's [X]..."
- "At the end of the day..."
- "Moving forward..."

**Vague claims:**
- "widely recognized", "well-known", "highly regarded"
- "plays a crucial role", "serves as a testament to"
- "continues to inspire", "remains relevant today"

##### Content Red Flags

| Pattern | Problem | Fix |
|---------|---------|-----|
| **Generic descriptions** | Replacing specific facts with vague positivity | Add specific numbers, names, dates, examples |
| **Missing idioms** | No natural expressions or colloquialisms | Add phrases the user actually says |
| **No opinions** | Hedging everything, no strong takes | Include the user's actual opinions |
| **No imperfections** | Too polished, no rough edges | Keep some personality quirks |
| **Confident vagueness** | Authoritative tone with no specifics | Either be specific or acknowledge uncertainty |

##### Review Process

1. **Read aloud** - Does it sound like a person talking or a press release?
2. **Count the triads** - More than 1-2 per page? Rewrite.
3. **Search for red flag words** - Ctrl+F for "crucial", "delve", "landscape", etc.
4. **Check sentence variety** - Are lengths varied? Do some start differently?
5. **Find the opinions** - Can you identify the author's actual stance?
6. **Spot the specifics** - Are there concrete examples, numbers, names?

##### Rewrite Examples

**Before (AI-like):**
> "When it comes to karaoke, selecting the right song is crucial for delivering an engaging performance. This comprehensive guide will delve into the multifaceted aspects of song selection, exploring the various factors that play a pivotal role in creating a memorable experience."

**After (Human-like):**
> "Pick the wrong karaoke song and you'll bomb. I've seen it happen—someone ambitious tackles Bohemian Rhapsody and loses the crowd by the second verse. Here's how to avoid that."

**Before (AI-like):**
> "The platform offers a seamless, user-friendly experience that leverages cutting-edge technology to deliver robust functionality, comprehensive features, and innovative solutions."

**After (Human-like):**
> "It works. The search is fast, the interface stays out of your way, and I haven't hit a bug in six months of daily use."

After fixing AI patterns, do a final read-through with the user to confirm the content sounds authentically theirs.

### Phase 5: Technical SEO Elements

#### 5a. Generate Meta Elements

Create SEO metadata:

```
## SEO Elements

**Title Tag** (50-60 chars):
[Title with primary keyword]

**Meta Description** (150-160 chars):
[Compelling description with keyword]

**URL Slug**:
/[keyword-focused-slug]

**Schema Markup Suggestions**:
- [FAQPage schema if FAQ section]
- [Article schema for blog posts]
- [LocalBusiness schema if applicable]
```

#### 5b. Internal Linking Suggestions

Review existing site content and suggest internal links:
- Where should this new page link TO?
- What existing pages should link TO this new page?

### Phase 6: Implementation

#### 6a. Deliver Final Content

Provide the complete content package:
- Full page content in markdown
- Meta title and description
- Suggested internal links
- Schema markup if applicable

#### 6b. Offer Implementation Help

```
## Ready to Publish?

I can help you:
1. **Create the file** in your codebase
2. **Update navigation** to include this page
3. **Add internal links** from existing pages
4. **Set up redirects** if replacing/consolidating content

What would you like to do next?
```

## Interview Best Practices

**DO:**
- Ask open-ended questions that elicit stories and examples
- Listen for unique phrases and terminology the user naturally uses
- Dig deeper when they mention something interesting ("Tell me more about...")
- Capture specific numbers, dates, names when mentioned
- Note strong opinions - these make content distinctive

**DON'T:**
- Accept generic answers - push for specifics
- Put words in their mouth - use THEIR words
- Skip the interview to save time - it's the whole point
- Generate content that could be from anyone

## Quality Checklist

Before delivering final content, verify:

**Authenticity (from interview):**
- [ ] Contains specific examples from the user's experience
- [ ] Includes opinions/recommendations unique to the user
- [ ] Uses terminology and phrases natural to the user
- [ ] Provides value beyond what generic AI could produce

**AI Pattern Review (Phase 4c):**
- [ ] No rule-of-three overuse (triads limited to 1-2 per page)
- [ ] Em dashes used sparingly, not in place of commas
- [ ] No trailing importance claims ("emphasizing the significance...")
- [ ] Red flag words eliminated (delve, crucial, landscape, leverage, etc.)
- [ ] Sentence lengths varied (mix of short and long)
- [ ] Specific facts present, not just generic positive descriptions
- [ ] Content sounds like a person, not a press release (read aloud test)

**SEO Elements:**
- [ ] Answers questions searchers actually have (from GSC data)
- [ ] Has proper heading hierarchy for SEO
- [ ] Includes relevant internal linking opportunities
- [ ] Has compelling meta title and description

## Related Commands

| Command | Purpose |
|---------|---------|
| `/seo-review` | Identify content opportunities from search data |
| `/plan` | Plan larger content strategy |
| `/shipit` | Publish content changes |
