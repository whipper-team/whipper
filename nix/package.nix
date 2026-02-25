{
  lib,
  python3,
  fetchFromGitHub,
  fetchpatch,
  installShellFiles,
  wrapGAppsNoGuiHook,
  gobject-introspection,
  libcdio-paranoia,
  cdrdao,
  libsndfile,
  glib,
  flac,
  sox,
  util-linux,
  testers,
  whipper,
}:
let
  bins = [
    libcdio-paranoia
    cdrdao
    flac
    sox
    util-linux
  ];
in
python3.pkgs.buildPythonApplication rec {
  pname = "whipper";
  version = "0.10.0";
  pyproject = true;

  src = ./..;

  nativeBuildInputs = [
    gobject-introspection
    installShellFiles
    wrapGAppsNoGuiHook
  ];

  build-system = with python3.pkgs; [
    docutils
    setuptools-scm
  ];

  propagatedBuildInputs = with python3.pkgs; [
    discid
    musicbrainzngs
    mutagen
    packaging
    pillow
    pycdio
    pygobject3
    ruamel-yaml
    setuptools
  ];

  buildInputs = [
    libsndfile
    glib
  ];

  nativeCheckInputs =
    with python3.pkgs;
    [
      pytestCheckHook
      twisted
    ]
    ++ bins;

  makeWrapperArgs = [
    "--prefix"
    "PATH"
    ":"
    (lib.makeBinPath bins)
    "\${gappsWrapperArgs[@]}"
  ];

  dontWrapGApps = true;

  outputs = [
    "out"
    "man"
  ];
  postBuild = ''
    make -C man
  '';

  preCheck = ''
    # disable tests that require internet access
    # https://github.com/JoeLametta/whipper/issues/291
    substituteInPlace whipper/test/test_common_accurip.py \
      --replace "test_AccurateRipResponse" "dont_test_AccurateRipResponse"
    export HOME=$TMPDIR
  '';

  postInstall = ''
    installManPage man/*.1
  '';

  passthru.tests.version = testers.testVersion {
    package = whipper;
    command = "HOME=$TMPDIR whipper --version";
  };

  meta = {
    homepage = "https://github.com/whipper-team/whipper";
    description = "CD ripper aiming for accuracy over speed";
    maintainers = with lib.maintainers; [ mib ];
    license = lib.licenses.gpl3Plus;
    platforms = lib.platforms.unix;
    mainProgram = "whipper";
  };
}
