# watkit
a package registry for handwritten WAT modules with recursive dependency resolution, semantic versioning, and automatic runner generation (JS + rust). 
cli first, pretty website second <3

## why?
∵ WAT is a very cool low level language, and the first of its kind with such a low barrier to entry (runs in browser!).  
∵ more people writing WAT by hand = more people using optimized WASM = a faster web.  
∵ less rewriting of "standard" code = more time for people to innovate with WAT.

## what does watkit include?
everything you'd expect from a package registry! that means: a cli, a website to browse packages, a way to publish packages, and a consistent package format. if you're familiar with npm, you'll feel right at home. 

## best features: 
✰ auto-generates js and rust runners for entire WAT projects, including resolving recursive dependency trees handling multiple wasm package versions  
✰ handles remote and local imports into a main wasm file enabling glued-together multi-file publishable WAT modules that stay together when imported into another project

## install guide
install is incredibly simple: make sure you have python3.7 or greater on your system and these packages (for unix): 
```python
os
sys
subprocess
shutil
platform
from pathlib import Path
```
for windows, you'll also need winreg.  
then, download the install file for your OS from this repo and run it as: 
```bash 
# for unix
python3 main.py
```  

```powershell 
# for windows
python3 main_windows.py
```
follow the install instructions, and choose the cli-only install for quickstart. serverside code is provided in this repo to make this project open-source and build trust with the community, but is not needed for most use cases.

> **Note:** you do not need to clone the repo beforehand. the install file will do that for you.

## commands overview
### `watkit init`
initializes a new watkit project. in a specified directory (or the current one if none is specified), creates a new watkit.json file with the following structure:
```json
{
  "name": "my-package",
  "version": "0.1.0",
  "main": "src/main.wat",
  "output": "dist/main.wasm",
  "description": "a new web assembly text format module.",
  "author": "this'll be you :D",
  "license": "MIT"
}
```
also, creates a template src/main.wat file with the following content:
```wat
(module
  (func (export "add") (param i32 i32) (result i32)
    local.get 0
    local.get 1
    i32.add
  )
)
```
finally, creates a readme.md file for you to fill out when you're ready to publish!

### `watkit login`
initiates a login flow with github's device flow oauth (similar to the login button on the website, but for a cli rather than a browser). at the end of the flow, you'll be able to publish packages to the registry, since that's an authenticated action.

### `watkit logout`
logs you out of the registry by deleting the JWT used by our server to authenticate you.

### `watkit pack`
packages your project into a .watpkg archive, but does not upload it. this is useful if you want to inspect or distribute your package manually. the resulting archive includes: your watkit.json manifest, any .wat files in src/, and any top-level files like README.md. the output file will be saved as:
```
dist/<package-name>-<version>.watpkg
```
.watpkg archives are just tar.gz files, so you can extract them with your favorite archive manager (although, the watkit install cli handles all the extraction for you when installing from the remote registry).

### `watkit compile`
compiles your main .wat file into a .wasm binary. does not resolve imports — this is a standalone build.

based on paths in watkit.json, e.g.:
```json
{
  "main": "src/main.wat",
  "output": "dist/main.wasm"
}
```

### `watkit publish`
builds your .watpkg (like pack) and uploads it to the watkit registry. your package will then be available via watkit install.  
requirements:  
➜ you must be logged in (watkit login)  
➜ version must be new  
➜ project must have a valid watkit.json and compile cleanly

### `watkit install`
installs a package from the watkit registry into your project.  
packages are stored under `pkg/` and can be imported in your `.wat` files using the `pkg/your_pkgvversion` convention. can be called as either of:
```bash
watkit install math_utils
watkit install math_utilsv0.2.1
```

if you leave out the version (e.g., math_utils), watkit will fetch the latest available version. the .watpkg archive is downloaded, extracted, and compiled. dependencies (global, and local to the package being installed) are validated recursively. for a command like the above, modules would be installed into: pkg/math_utilsv0.2.1/. 
this behavior allows you to import modules into new wat like so:
```wasm
(import "pkg/math_utilsv0.2.1" "abs_i32" (func $abs_i32 (param i32) (result i32)))
```
### `watkit uninstall`
removes an installed package from the project directory by deleting its folder, when that package is specified by name AND version (needed to handle possible multiple versions). 

### `watkit run`

compiles your main.wat, resolves all dependencies in pkg/, and generates a runner in the language you choose. used like so:
```
watkit run --lang js
watkit run --lang rust
```
supports --lang js or --lang rust, generates a file like:
```
dist/run.mjs  // (for js)
dist/run.rs   // (for rust)
```
local and global imports are linked automatically by watkit using syntax from WebAssembly's import system. wasm modules from pkg/ are loaded and linked as needed. for a very simple dependency tree, the outputted JS might look like this: 

```javascript
const main = await WebAssembly.instantiate(mainWasm, {
  ["pkg/math_utilsv0.2.1"]: { abs_i32: math_utils.instance.exports.abs_i32 }
});
```

### `watkit search`

search for packages in the watkit registry by name or by author, like so:
```
watkit search "math" --name
watkit search "alice" --author
```
performs a fuzzy match (partial + approximate matches), and searches a pre-built index hosted by the watkit API (not on S3). 
returns a list of packages, including: name, author, latest version and all available versions. 
