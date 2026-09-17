class Newyt < Formula
  include Language::Python::Virtualenv

  desc "Terminal YouTube client: your feed, watch later, and history with ASCII thumbnails"
  homepage "https://github.com/Chuckle-Rollston/newyt"
  # Once you've cut a release tag (e.g. v0.1.0), replace the sha256 below with
  # the real checksum:
  #   curl -L -o newyt.tar.gz https://github.com/Chuckle-Rollston/newyt/archive/refs/tags/v0.1.0.tar.gz
  #   shasum -a 256 newyt.tar.gz
  url "https://github.com/Chuckle-Rollston/newyt/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "REPLACE_WITH_REAL_SHA256"
  license "MIT"

  depends_on "python@3.12"

  def install
    venv = virtualenv_create(libexec, "python3.12")
    venv.pip_install_and_link buildpath
    system libexec/"bin/python3", "-m", "playwright", "install", "chromium"
  end

  def caveats
    <<~EOS
      Before first use, log in to YouTube (opens a real browser window once):
        newyt login

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
