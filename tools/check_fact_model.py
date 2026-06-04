"""兼容 wrapper — 迁移到 ldvh_fact_validate.py，保留旧入口"""
from ldvh_fact_validate import main  # noqa: F401

if __name__ == "__main__":
    main()
