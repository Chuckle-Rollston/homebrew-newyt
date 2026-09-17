class Newyt < Formula
  include Language::Python::Virtualenv

  desc "Terminal YouTube client: your feed, watch later, and history with ASCII thumbnails"
  homepage "https://github.com/Chuckle-Rollston/newyt"
  url "https://github.com/Chuckle-Rollston/newyt/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "284e487f7a50ee8373d964ff9daa2d36e11dea857e116834c8824c9d28a72f7b"
  license "MIT"

  depends_on "python@3.12"

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
      Before first use, log in to YouTube:
        newyt login

      This opens a real browser window once so you can sign in, and will
      also download the Chromium browser Playwright needs (one-time,
      ~150-200MB) if it isn't already present.

      Then launch the app:
        newyt

      Your login is stored only in a local browser profile on this machine
      and is only used to read your home feed, watch later, and history.
      Videos always open in a separate private/incognito window, signed out.
    EOS
  end

  test do
    system "#{bin}/newyt", "--help"
  end
end
