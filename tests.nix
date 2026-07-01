{
  lib,
  stdenvNoCC,
  fake-pkg-config,
  pkg-config,
}:
let
  mkTest = lib.extendMkDerivation {
    constructDrv = stdenvNoCC.mkDerivation;

    excludeDrvArgNames = [
      "name"
      "test"
    ];

    extendDrvArgs =
      finalAttrs:
      {
        name,
        test,
        withPkgConfig ? false,
        ...
      }:
      {
        pname = name + "-test";
        version = "none";

        strictDeps = true;
        __structuredAttrs = true;

        nativeCheckInputs = [
          fake-pkg-config
        ]
        ++ lib.optionals withPkgConfig [
          pkg-config
        ];

        dontUnpack = true;

        checkPhase = test;

        installPhase = ''
          touch "$out"
        '';
      };
  };
in
{
  basic = mkTest {
    name = "basic";

    test = ''
      fake-pkg-config --libs --cflags libzstd
    '';
  };
}
