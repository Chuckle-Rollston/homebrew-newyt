class Newyt < Formula
  include Language::Python::Virtualenv

  desc "Terminal YouTube client: your feed, watch later, and history with ASCII thumbnails"
  homepage "https://github.com/Chuckle-Rollston/homebrew-newyt"
  url "https://github.com/Chuckle-Rollston/homebrew-newyt/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "e0ffe959b5bbf059c5beb5d0792224d141e82622a03dad3b857a8eaed67b2ca1"
  license "MIT"

  depends_on "python@3.12"
  depends_on "ffmpeg"

  def install
    venv = virtualenv_create(libexec, "python3.12")
    # venv is created --without-pip, so install via the outer interpreter's
    # pip pointed at the venv (Homebrew's own pattern), not a nonexistent
    # libexec/bin/pip. Homebrew's resource/pip_install helpers always force
    # --no-binary (source builds, dragging in a cmake/ninja toolchain for
    # packages like greenlet/pillow), so install straight from PyPI instead,
    # restricted to prebuilt wheels only, so no compiler is ever needed.
    python = Formula["python@3.12"].opt_bin/"python3.12"
    system python, "-m", "pip", "--python=#{venv.root}/bin/python",
           "install", "--verbose", "--only-binary=:all:",
           buildpath
    bin.install_symlink venv.root/"bin/newyt"
  end

  def caveats
    <<~EOS
      Before first use, import your YouTube session from a browser you're
      already signed into (default: Chrome; add --browser firefox/brave/
      edge/safari/opera for another one):
        newyt login

      Then launch the app:
        newyt

      The first time you read a tab, this also downloads Chromium for
      Playwright (one-time, ~150-200MB), used only to read your feed,
      watch later, and history.

      Playing a video (Enter) never loads youtube.com itself: it uses
      yt-dlp + ffmpeg (installed as a dependency) to fetch and play the
      video directly with your default player, or with VLC if installed
      (instant streaming start, no download wait).
    EOS
  end

  test do
    system "#{bin}/newyt", "--help"
  end
end
