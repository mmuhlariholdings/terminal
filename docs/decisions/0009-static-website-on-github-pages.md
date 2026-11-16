# 0009. Static website on GitHub Pages

- **Status:** Proposed
- **Date:** 2026-11-16
- **Decided by:** Proposed by the AI assistant; awaiting owner approval

## Context

The project needs a public landing page that markets Terminal 1, shows the Onshape model and sends people to the repository.
The Finish Line site ran on Heroku with a database for sign-ups; an open project has no sign-up list to protect and benefits from
anyone being able to preview and improve the site.

## Decision

A **static site in `website/public/`**, deployed to **GitHub Pages** by `.github/workflows/website.yml` on every push to `main`
that touches `website/`. Interest is captured by GitHub stars, watches and Discussions instead of a form.

## Consequences

- No servers, databases or secrets; contributors preview with `python3 -m http.server`.
- A custom domain can be added later in the repository's Pages settings.
- No private sign-up list; if one is wanted later, it needs a new record.

## Alternatives considered

- **Heroku + MongoDB (as Finish Line):** a running cost and secrets for a form we don't need yet.
- **A site builder (Framer, Webflow):** fast to make, but closed and not reviewable in pull requests.

## How we check it

The website workflow deploys on merge; the site loads on a phone and a desktop with no console errors.

## Related

`website/README.md`; `.github/workflows/website.yml`.
