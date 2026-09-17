class Newyt < Formula
  include Language::Python::Virtualenv

  desc "Terminal YouTube client: your feed, watch later, and history with ASCII thumbnails"
  homepage "https://github.com/Chuckle-Rollston/newyt"
  url "https://github.com/Chuckle-Rollston/newyt/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "c946f721de0bdc86e20cf630d3f3b45503001fe76edd2494289f78f672b5992d"
  license "MIT"

  depends_on "python@3.12"

  def install
    venv = virtualenv_create(libexec, "python3.12")
    # Homebrew's Language::Python::Virtualenv resource helpers force
    # --no-binary, which requires source builds (and drags in a cmake/ninja
    # toolchain for packages like greenlet/pillow). This tap installs
    # straight from PyPI instead, restricted to prebuilt wheels only, so no
    # compiler is ever needed.
    system venv.root/"bin/pip", "install", "-v",
           "--only-binary=:all:",
           buildpath
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
