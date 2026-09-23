# Push path — unblock empty Troubadourcode/svinn-human

Cloud Agents refuse empty repos (`This repository is empty. Add an initial commit…`).  
Someone with **write** access to the GitHub repo must push this tree once.

## Exact commands (from a machine with `gh`/`git` auth to Troubadourcode)

```bash
# 1) Copy scaffold (adjust source path if you pulled from the bot box)
cp -a /path/to/svinn-human-scaffold /tmp/svinn-human
cd /tmp/svinn-human

# 2) First commit on main
git init -b main
git add .
git commit -m "chore: initial IRI scaffold (Case API stub, docs, Apache-2.0)"

# 3) Point at the empty GitHub repo and push
git remote add origin https://github.com/Troubadourcode/svinn-human.git
git push -u origin main
```

If the remote already has a README from the GitHub UI, use:

```bash
git pull origin main --allow-unrelated-histories
# resolve if needed, then:
git push -u origin main
```

## After push

1. Re-launch Cloud Agent on `https://github.com/Troubadourcode/svinn-human`
2. Platform owns `packages/case-api/` — expand OpenAPI + implement observe stub
3. Delete this `PUSH.md` in a follow-up commit if desired

## Archive for handoff

On the CTO box the tree lives at:

`/workspace/svinn-human-scaffold/`

Tar for transfer:

```bash
cd /workspace && tar -czf svinn-human-scaffold.tgz svinn-human-scaffold
```

## Enum note

Case OpenAPI uses **Platform** CaseStatus names (not CTO shorthand). See `packages/case-api/ENUM-MAP-CTO.md`.
