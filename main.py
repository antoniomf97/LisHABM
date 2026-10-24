"""Entry point: python main.py <config-name>  ->  configs/simulation/<name>.yaml"""

from orchestration.runner import main

if __name__ == "__main__":
    raise SystemExit(main())
