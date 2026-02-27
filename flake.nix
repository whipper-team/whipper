{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      inherit (nixpkgs) lib;
    in
    {
      packages = lib.genAttrs lib.systems.flakeExposed (system: rec {
        default = whipper;
        whipper = nixpkgs.legacyPackages.${system}.callPackage ./nix/package.nix { };
      });
    };
}
