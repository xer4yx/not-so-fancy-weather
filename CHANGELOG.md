# CHANGELOG


## v1.5.2-rc.1 (2025-02-04)

### Chores

- **versioning**: Fixed versioning configuration
  ([`d3ce6db`](https://github.com/xer4yx/not-so-fancy-weather/commit/d3ce6db1ef2661a54447b89864bd656a5e452e02))

## Changes

- Other branches can now update version

- Added version-bump.yml


## v1.5.1 (2025-02-03)

### Chores

- Added node_modules to .gitignore
  ([`b9eab7a`](https://github.com/xer4yx/not-so-fancy-weather/commit/b9eab7a3ae35af911a220d044bf2d1cb237fd10b))

### Features

- **cors**: Added frontend address to allowed origin in CORS
  ([`dbe1a41`](https://github.com/xer4yx/not-so-fancy-weather/commit/dbe1a411f451b0d2bfe2884dd134c47f410cf0de))

- **frontend**: Added a frontend template
  ([`55d2581`](https://github.com/xer4yx/not-so-fancy-weather/commit/55d2581551de8a83422a76c366c12c642c8ccfb6))

This resolves #7

- **map**: Added map visualization to searched place
  ([`c7e8674`](https://github.com/xer4yx/not-so-fancy-weather/commit/c7e86749232c74ded17adb7531903bed63ef11b2))

- **router**: Added crud operations and user router
  ([`e22ba02`](https://github.com/xer4yx/not-so-fancy-weather/commit/e22ba0251a08681f8520a08cd06a75ac0e1497a3))

Created a user endpoint for database operations

This resolves #12


## v1.3.0 (2025-01-31)

### Features

- **interfaces**: Changed static to dynamic querying on api
  ([`94e413b`](https://github.com/xer4yx/not-so-fancy-weather/commit/94e413b5cd928538aa621a18a14d9226b1b04480))


## v1.2.0 (2025-01-31)

### Features

- **infrastructure**: Modified func to class method and added a dependency injection
  ([`2a9faa2`](https://github.com/xer4yx/not-so-fancy-weather/commit/2a9faa229d46cf6791a9cdb2647b7c57d6794667))


## v1.1.0 (2025-01-31)

### Chores

- Update .gitignore to ignore environment files and venv
  ([`a129dc2`](https://github.com/xer4yx/not-so-fancy-weather/commit/a129dc2046e7bad34ab5f550fc8ba67f72b1ef04))

- **toml**: Changed pyproject.toml encoding to UTF-8
  ([`7ee6c8b`](https://github.com/xer4yx/not-so-fancy-weather/commit/7ee6c8ba07cbe0e18ef71efbf833ef78d1f8875f))

### Features

- **app**: Added FastAPI app, routers, tools & utils
  ([`656791b`](https://github.com/xer4yx/not-so-fancy-weather/commit/656791bded501777ec512ff2d697f71a4a1652cf))

- **core**: Added abstract class for concrete api classes implementation
  ([`1cc360b`](https://github.com/xer4yx/not-so-fancy-weather/commit/1cc360b680884164e5b568113e3b696ce27143c3))
