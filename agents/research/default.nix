{ python3Packages }:

python3Packages.buildPythonApplication {
  pname = "research-agent";
  version = "0.1.0";
  pyproject = true;
  src = ../..;

  build-system = [ python3Packages.setuptools ];

  pythonImportsCheck = [ "research_agent" ];
}
