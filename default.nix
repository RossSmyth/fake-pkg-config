{
  system ? builtins.currentSystem or "x86_64-linux",
  inputs ? (import ./npins { }),
  pkgs ? import inputs.nixpkgs {
    inherit system;
  },
}:
let
  lib = pkgs.lib;

  fs = lib.fileset;

  source = fs.unions [
    ./src
  ];
in
pkgs.stdenvNoCC.mkDerivation (finalAttrs: {
  pname = "fake-pkg-config";
  version = "0.1";

  strictDeps = true;
  __structuredAttrs = true;

  src = fs.toSource {
    root = ./src;
    fileset = source;
  };

  nativeBuildInputs = with pkgs; [
    makeBinaryWrapper
  ];

  installPhase = ''
    mkdir -p "$out/bin"

    install -Dm744 fake-pkg-config.bash "$out/bin/.fake-pkg-config"

    makeWrapper "${lib.getExe pkgs.bashNonInteractive}" "$out/bin/fake-pkg-config" \
      --add-flags "-euo pipefail $out/bin/.fake-pkg-config"

    ln -s "$out/bin/fake-pkg-config" "$out/bin/pkg-config"    
  '';

  passthru.tests = pkgs.callPackage ./tests.nix { fake-pkg-config = finalAttrs.finalPackage; };

  meta.mainProgram = "fake-pkg-config";
})
