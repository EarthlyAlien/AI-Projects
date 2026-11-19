# Efficient AI / blog images for business + tech storytelling

## What we researched first

| Source | Technique we kept |
|--------|-------------------|
| [Semrush — AI images in posts](https://www.semrush.com/kb/1557-how-to-enhance-your-blog-posts-with-ai-images) | Prefer **diagrams** for process / comparison beats |
| [Patrick Wings — B2B visual storytelling](https://www.patrickwings.com/en/insights/b2b-visual-storytelling/) | One sentence message; **one job per graphic**; before/after |
| [BrandGene — SaaS blog illustrations](https://brandgene.io/blog/ai-image-generation/article-illustrations/ai-illustrations-for-saas-blog-posts) | No generic laptop people; no fake product UI |
| [Floniks SaaS visuals playbook](https://floniks.com/learn/playbooks/saas-marketing-visuals-playbook) | Lock palette + abstraction; conceptual > stock photo |
| [CapCut — AI images for tech blogs](https://www.capcut.com/ideas/ai-image/ai-image-for-tech-blogs) | One-sentence brief before making the asset |
| [Ilir Ivezaj — enterprise prompt templates](https://ilirivezaj.com/ai/stable-diffusion-enterprise) | Reusable template; **overlay text programmatically** |
| [Genlaxy — blog headers](https://genlaxy.ai/blog/blog-header-images-with-ai) | One recipe; change only the concept |

Photoreal “mood stills” and unlabeled flat icons both failed storytelling for this article. Business/tech readers need the claim readable in two seconds.

## Locked production recipe (what we ship)

Render with `python3 evals/render_article_images.py` (Pillow diagrams):

1. Write a one-sentence brief per frame  
2. Fixed palette: cool-gray `#F1F3F6`, navy `#1A2B4A`, amber `#E88C24`  
3. Diagram types only: before/after, process ladder, mismatch ≠, dual chart  
4. Short witty labels drawn in code (no AI typography)  
5. 1920×1080, same margins, same type scale  

## Frame briefs

1. Same model. Different blast radius. — sticky note vs checklist shield  
2. Vibe checks are a feature when dinner is the stakeholder  
3. Enterprise surface area breaks vibes — tickets through a cracked funnel  
4. Invented chatbot refund ≠ real policy  
5. Ladder: vibe → 10–20 cases → prod traces  
6. Practice list climbs; fresh tickets stay flat  
