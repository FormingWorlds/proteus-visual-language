# Repository setup

One-time steps to take this folder from a local checkout to a published,
releasable repository. Automation lives in
[`.github/workflows/pages.yml`](.github/workflows/pages.yml) (brand-guide
deployment), [`.github/workflows/release.yml`](.github/workflows/release.yml)
(npm + PyPI publishing), and
[`.github/workflows/tokens.yml`](.github/workflows/tokens.yml) (token sync
check).

## 1. Create the repository

```bash
git init
git add -A
git commit -m "PROTEUS Visual Language v1.0 (Thermocline)"
gh repo create FormingWorlds/proteus-visual-language --public --source=. --push
```

Without `gh`: create `FormingWorlds/proteus-visual-language` on github.com
(Public, no README/license/gitignore), then:

```bash
git remote add origin git@github.com:FormingWorlds/proteus-visual-language.git
git push -u origin main
```

## 2. Enable GitHub Pages

Settings → Pages → Build and deployment → Source: **GitHub Actions**.
Every push to `main` then runs [`pages.yml`](.github/workflows/pages.yml),
which exports `brand-guide.pdf` and deploys the interactive guide to
https://formingworlds.github.io/proteus-visual-language.

## 3. Publishing prerequisites (before the first release)

**npm** (`@formingworlds/proteus-tokens`, from [`tokens/`](tokens/)):

- [ ] Create the `formingworlds` org on npmjs.com (or confirm access).
- [ ] Generate a granular automation token with publish rights for the org.
- [ ] Add it as the `NPM_TOKEN` repository secret
      (Settings → Secrets and variables → Actions → New repository secret).

**PyPI** (`proteus-mpl`, from [`figures/proteus-mpl/`](figures/proteus-mpl/)):

- [ ] On pypi.org: Publishing → Add a new pending publisher (Trusted
      Publisher, GitHub Actions) with project `proteus-mpl`, owner
      `FormingWorlds`, repository `proteus-visual-language`, workflow
      `release.yml`. No token or secret is needed.

## 4. Cut a release

Versioning is CalVer, `YY.MM.DD`, matching the wider PROTEUS ecosystem.

1. Set the version (without leading zeros, e.g. `26.7.12`; npm and PyPI
   reject padded forms) in [`tokens/package.json`](tokens/package.json) and
   [`figures/proteus-mpl/pyproject.toml`](figures/proteus-mpl/pyproject.toml).
2. Update [`CHANGELOG.md`](CHANGELOG.md).
3. Tag and push:

```bash
git tag 26.07.12
git push origin main --tags
```

The tag triggers [`release.yml`](.github/workflows/release.yml), which
publishes both packages.
