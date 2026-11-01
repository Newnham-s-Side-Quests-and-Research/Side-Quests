# Newnham's Side Quests

This repository brings together Lewis Newnham's engineering portfolio and research projects. It covers autonomous systems, software, AI and quantitative research.

## The projects

The [project index](programme-plan.md) introduces the twelve projects and their proposed order. Each folder in [projects](projects/) links to the corresponding plan, engineering pack and original portfolio documents.

The drone is an earlier build whose evidence still needs to be recovered. The other projects are research plans. The project folders do not yet contain implementations or verified results.

## Repository guide

- [Projects](projects/) contains a folder for each project.
- [Engineering packs](engineering-packs/) contain proposed requirements, designs and verification plans.
- [Plans](plans/) contain the original build plans and the evaluation harness specification.
- [Original portfolio](source/Engineering%20Portfolio/) contains the supplied project briefs and case studies.
- [Engineering standard](engineering-standard.md) sets out the approach to design, testing and review.

The [HTML plans](html-plans/index.html) are available for local reading. Download or clone the repository and open the index in a browser.

## Current status

The plans are a foundation for design and implementation. Each project still needs its open decisions and acceptance criteria reviewed. The drone also depends on recovering the original files. The Workflow Evaluation Harness is the proposed first build.

## Regenerate the HTML plans

Run `python -m pip install -r html-plans/requirements.txt` from the repository folder. Then run `python html-plans/generate.py`.
