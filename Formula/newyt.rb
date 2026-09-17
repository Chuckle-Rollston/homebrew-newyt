class Newyt < Formula
  include Language::Python::Virtualenv

  desc "Terminal YouTube client: your feed, watch later, and history with ASCII thumbnails"
  homepage "https://github.com/Chuckle-Rollston/newyt"
  url "https://github.com/Chuckle-Rollston/newyt/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "c946f721de0bdc86e20cf630d3f3b45503001fe76edd2494289f78f672b5992d"
  license "MIT"

  depends_on "python@3.12"

  # All resources below are pinned to prebuilt wheels (no compiler needed at
  # install time); several of these (greenlet, pillow, charset-normalizer)
  # have C extensions whose sdists pull in a heavy build toolchain, which is
  # unnecessary and slow when a wheel already exists for this platform.
  resource "certifi" do
    url "https://files.pythonhosted.org/packages/0b/a7/71ac2cff56fec219ed242bb11b8efb69fcc4bec75db06fb7bfe35de520e6/certifi-2026.7.22-py3-none-any.whl"
    sha256 "62f22742b58a1a33014a2b6b706588a8d7e2a88ae7bd1a6ebe8c992928483775"
  end

  resource "charset-normalizer" do
    url "https://files.pythonhosted.org/packages/30/27/78873dc8b6a56357517b74b6bb9568b80450e7bb4f6ef7e3fa9d22aa0bd7/charset_normalizer-3.5.1-cp312-cp312-macosx_10_13_universal2.whl"
    sha256 "5b6d1386bf0096d26d3a863dc0a487a5b4eb9aa93cf5ba69683d29dde6b9d60f"
  end

  resource "greenlet" do
    url "https://files.pythonhosted.org/packages/72/18/3fc6d951466ae9a2a688edcddde3b2e388da0a8244e0caf7117bbeb0eb95/greenlet-3.5.6-cp312-cp312-macosx_11_0_universal2.whl"
    sha256 "a5876d0a60355af98d535c47f6cd6eb0f8a432396dab26845d380b92f8412422"
  end

  resource "idna" do
    url "https://files.pythonhosted.org/packages/57/b0/0e52c878c53f245edd3a11020f20979b3f490f245af532c7cae3027754b5/idna-3.19-py3-none-any.whl"
    sha256 "815e7be7a7806d54abb586dc943addc79e8b2ee16915059658cbeff4b1b43bf4"
  end

  resource "pillow" do
    url "https://files.pythonhosted.org/packages/d8/66/9a386a92561f402389a4fc70c18838bf6d35eb5eb5c6850b4b2dc64f5048/pillow-12.3.0-cp312-cp312-macosx_11_0_arm64.whl"
    sha256 "ffd0c5368496f41b0944be820fcb7a838aa6e623d250b01acf2643939c3f99d7"
  end

  resource "playwright" do
    url "https://files.pythonhosted.org/packages/94/11/dc5c13fa1602371603acd461be47529c1b3513815d3a0dc98f642c291a10/playwright-1.63.0-py3-none-macosx_11_0_universal2.whl"
    sha256 "c89fc4736502a1f0fac2c8ca5d10c0cbc1c669f1f4774a2d8507a43140e4d53f"
  end

  resource "pyee" do
    url "https://files.pythonhosted.org/packages/a0/c4/b4d4827c93ef43c01f599ef31453ccc1c132b353284fc6c87d535c233129/pyee-13.0.1-py3-none-any.whl"
    sha256 "af2f8fede4171ef667dfded53f96e2ed0d6e6bd7ee3bb46437f77e3b57689228"
  end

  resource "requests" do
    url "https://files.pythonhosted.org/packages/a0/f4/c67b0b3f1b9245e8d266f0f112c500d50e5b4e83cb6f3b71b6528104182a/requests-2.34.2-py3-none-any.whl"
    sha256 "2a0d60c172f83ac6ab31e4554906c0f3b3588d37b5cb939b1c061f4907e278e0"
  end

  resource "typing-extensions" do
    url "https://files.pythonhosted.org/packages/49/d3/b8441a820a491ddfc024b0b0cf0393375b75ea13866d9c66727e54c2fc80/typing_extensions-4.16.0-py3-none-any.whl"
    sha256 "481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8"
  end

  resource "urllib3" do
    url "https://files.pythonhosted.org/packages/92/9d/c4e665119135114480843e7ab388fa94d8480650450e6f8e26b70d323a4c/urllib3-2.8.0-py3-none-any.whl"
    sha256 "0cf3cae568d36aa9576b28dfb35f11328f1cb974ca7647d9475ebb86c75ac6e3"
  end

  def install
    virtualenv_install_with_resources
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
