Please read the following guidelines for contributors:

How are the files in the repository maintained and used?

- We create PRs to `main` and then manually merge from `main` to `v0`.
- We then use reusable scripts located in the `v0` branch.

Where are the `.github/workflows` used?

- `_tests-on-pr.yml` is used in `scikit-package`.
- `_tests-on-pr-no-codecov-no-headless.yml` is used in `skpkg-package-system`. It does not include Codecov, builds, or headless testing.
