# fake-pkg-config

Because lying is actually good and fun.

## What this does

It is common in Rust `build.rs` scripts to do something like:
1. Using pkg-config-rs, see if a lib exists
2. If it does exist, use the system lib
3. If it does not exist, fallback to just compiling it with cc-rs/cmake-rs

In Nixpkgs we do not want the fallback to occur. So this just replies "yes that definitly exists and here's the flags for doing it," under the assumption that the build will then proceed to fail until you add such libraries into the build closure. 

It does have a passthru, so if pkg-config is also in the build closure, it will ask "does this actually exist", and if it does it will just pass-through all the queries to pkg-config so it will compile correctly.
