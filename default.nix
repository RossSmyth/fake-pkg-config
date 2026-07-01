{
  system ? builtins.currentSystem or "x86_64-linux",
  inputs ? (import ./. npins { }),
  pkgs ? import inputs.nixpkgs {
    inherit system;
  };
}:
let
  lib = pkgs.lib;

  fs = lib.filesets;

  source = fs.unions [
    ./src
  ];
in
pkgs.stdenvNoCC (finalAttrs: {
  pname = "fake-pkg-config";
  version = "0.1";

  src = fs.toSource {
    root = ./src;
    fileset = source;
  };

  installPhase = ''
      mkdir -p "$out/bin"

      cp ./fake-pkg-config.bash "$out/bin"
    '';
})
