if [[ -n "${DEBUG:-}" ]]; then set -x; fi

# Find a pkg-config on PATH
getPkgConfig() {
  if command -v pkg-config; then
    echo "pkg-config"
  elif command -v pkgconf; then
      echo "pkgconf"
  else
    echo ""
  fi
}

# Some flags are mutually exclusive
doneModversion=false
doneFlags=false
doneVariables=false

# Get a fake prefix to output things to
readonly fakePrefix="$(mktemp -du nixpkgs.XXXXX)"

# pkg-config processes on a per-arg basis
# This means that for every library, all --libs are output,
# The for each library, all --cflags are output.
#
# So we take in an arg, then all trailing args are the libs
# And we just output some nonsense. Hopefully that fails the builds.
#
# $1: Arg, currently `--modversion`, `--variable`, `--libs`, and `--cflags` are handled
# $*: library names
fakeOutput() {
  # The arg is the first arg
  readonly arg="$1"


  # Shift to the libraries to process
  shift

  local output=()

  case "$arg" in
    --modversion)
      if $doneFlags; then
        echo "--modversion is incompatible with --cflags and --libs, ignoring" >&2
        return 0
      elif $doneVariables; then
        echo "--modversion is incompatible with --variable, ignoring" >&2
        return 0
      else
        for lib in "$@"; do
          # Unsure of a good value
          output+=("1.0.0")
        done
      fi
      shift
      ;;
    --variable=*)
      local -r var="${1#*=}"

      if $doneFlags; then
        echo "--modversion is incompatible with --cflags and --libs, ignoring" >&2
        return 0
      elif [[ "$var" == "prefix" ]]; then
        for lib in "$@"; do
          output+=("$fakePrefix/$lib")
        done
      elif [[ "$var" == "libdir" ]]; then
        for lib in "$@"; do
          output+=("$fakePrefix/$lib/lib")
        done
      elif [[ "$var" == "includedir" ]]; then
        for lib in "$@"; do
          output+=("$fakePrefix/$lib/include")
        done
      else
        for lib in "$@"; do
          output+=("$fakePrefix/$lib/$var")
        done
      fi
      doneVariables=true
      shift
      ;;
    --libs)
      if $doneModversion; then
        echo "--libs is incompatible with --modversion, ignoring" >&2
        return 0
      elif $doneVariables; then
        echo "--libs is incompatible with --variable, ignoring" >&2
        return 0
      else
        for lib in "$@"; do
          output+=("-L$fakePrefix/$lib/lib -l$lib")
        done
        doneFlags=true
      fi

      shift
      ;;
    --cflags)
      if $doneModversion; then
        echo "--cflags is incompatible with --modversion, ignoring" >&2
      elif $doneVariables; then
        echo "--cflags is incompatible with --variable, ignoring" >&2
      else
        for lib in "$@"; do
          output+=("-I$fakePrefix/$lib/include")
        done
        doneFlags=true
      fi
      shift
      ;;
  esac

  echo "${output[*]}"
}

PKG_CONFIG="$(getPkgConfig 2>&1)"

# Check if the library exists or not
libExists() {
  local -r lib="$1"

  "$PKG_CONFIG" --exists "$1"
}

echo "Running fake-pkg-config" >&2

# pkg-config flags are position sensitive.
# So we must first collect all flags and libs,
# then do everything in order.
ARGS=()
FAKE_LIBS=()
REAL_LIBS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --*)
      # Anything starting with "--" is probably a flag
      ARGS+=("$1")
      shift
      ;;
    *)
      if libExists "$1" &> /dev/null; then
        REAL_LIBS+=("$1")
      else
        FAKE_LIBS+=("$1")
      fi

      shift
      ;;
  esac
done

readonly ARGS REAL_LIBS FAKE_LIBS PKG_CONFIG

output=()
for arg in "${ARGS[@]}"; do
  output+=("$(fakeOutput "$arg" "${FAKE_LIBS[@]}")")

  if [[ -n "$PKG_CONFIG" && ${#REAL_LIBS[@]} -gt 0  ]]; then
    output+=("$("$PKG_CONFIG" "$arg" "${REAL_LIBS[@]}")")
  fi
done

echo "${output[*]}"
