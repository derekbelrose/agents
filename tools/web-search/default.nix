{ python3Packages }:

python3Packages.buildPythonApplication {
  pname = "web-search-tool";
  version = "0.1.0";
  pyproject = true;
  src = ./.;
  build-system = [ python3Packages.setuptools ];
  pythonImportsCheck = [ "web_search" ];
}
