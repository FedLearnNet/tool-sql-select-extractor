from pyfedappwrap.engine.runtime import FedDBEngine

from app import SqlSelectExtractorAPP

engine = FedDBEngine()

engine.register(SqlSelectExtractorAPP())

if __name__ == "__main__":
    engine.start()
    engine.wait_until_stop()
