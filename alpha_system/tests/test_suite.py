"""Test Suite — Validation complète du système Alpha."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_config():
    from alpha_system.config import CONFIG
    assert CONFIG["STARTING_CAPITAL"] == 1000
    assert CONFIG["CONFIDENCE_THRESHOLD"] == 0.75
    assert CONFIG["MAX_RISK_PER_TRADE"] == 0.02
    assert CONFIG["MAX_DRAWDOWN_PCT"] == 0.15
    assert CONFIG["MODE"] in ("DRY", "LIVE")
    print("  [OK] config")


def test_database():
    from alpha_system.memory.database import DatabaseManager
    db = DatabaseManager("alpha_system/data/test.db")
    db.save_state(1000, 1000, 0, 0, 0, 0)
    state = db.load_state()
    assert state is not None
    assert state["capital"] == 1000
    db.record_trade("test", "YES", 0.7, 1, 0.1, 0.85)
    assert db.get_trade_count() >= 1
    db.log_audit("TEST", "test entry")
    db.close()
    os.remove("alpha_system/data/test.db")
    print("  [OK] database")


def test_risk_engine():
    from alpha_system.config import CONFIG
    from alpha_system.risk.risk_engine_v2 import RiskEngineV2
    risk = RiskEngineV2(CONFIG)
    max_size = CONFIG["MAX_TRADE_SIZE"]
    ok, reason = risk.validate_trade(1000, min(10, max_size), 0.85)
    assert ok is True
    ok, reason = risk.validate_trade(1000, max_size + 500, 0.85)
    assert ok is False
    ok, reason = risk.validate_trade(1000, min(5, max_size), 0.40)
    assert ok is False
    # check_drawdown
    ok, _ = risk.check_drawdown(900)
    assert ok is True
    ok, _ = risk.check_drawdown(100)
    assert ok is False
    # check_loss_streak
    ok, _ = risk.check_loss_streak()
    assert ok is True
    for _ in range(6):
        risk.record_trade(-1)
    ok, _ = risk.check_loss_streak()
    assert ok is False
    # check_trade_limits
    risk2 = RiskEngineV2(CONFIG)
    ok, _ = risk2.check_trade_limits()
    assert ok is True
    # add/remove position
    risk2.add_position("test_market", 5, 0.7)
    assert "test_market" in risk2.get_positions()
    risk2.remove_position("test_market")
    assert "test_market" not in risk2.get_positions()
    print("  [OK] risk_engine_v2")


def test_confidence_manager():
    from alpha_system.config import CONFIG
    from alpha_system.ai.confidence_manager import ConfidenceManager
    cm = ConfidenceManager(CONFIG)
    ok, _ = cm.validate({"confidence": 0.90})
    assert ok is True
    ok, _ = cm.validate({"confidence": 0.30})
    assert ok is False
    ok, _ = cm.validate(None)
    assert ok is False
    print("  [OK] confidence_manager")


def test_cost_calculator():
    from alpha_system.config import CONFIG
    from alpha_system.execution.cost_calculator import CostCalculator
    cc = CostCalculator(CONFIG)
    ok, _ = cc.validate({"size": 10, "price": 0.8, "confidence": 0.9})
    assert ok is True
    ok, _ = cc.validate({"size": 0.1, "price": 0.51, "confidence": 0.65})
    assert ok is False
    costs = cc.calculate_total_cost(10, 0.8)
    assert "total_cost" in costs
    assert costs["total_cost"] > 0
    adjusted = cc.adjust_pnl(1.0, 10, 0.8)
    assert "adjusted_pnl" in adjusted
    print("  [OK] cost_calculator")


def test_error_handler():
    from alpha_system.protection.error_handler import ErrorHandler
    eh = ErrorHandler()
    result = eh.safe_execute(lambda: 42, default=0, context="test")
    assert result == 42
    result = eh.safe_execute(lambda: 1/0, default=-1, context="div_zero")
    assert result == -1
    assert eh.error_count == 1
    assert eh.is_system_healthy() is True
    print("  [OK] error_handler")


def test_kill_switch():
    from alpha_system.protection.kill_switch import KillSwitch
    ks = KillSwitch()
    assert ks.validate(900, 1000) is True
    assert ks.validate(800, 1000) is False
    print("  [OK] kill_switch")


def test_profit_optimizer():
    from alpha_system.ai.profit_optimizer import ProfitOptimizer
    po = ProfitOptimizer()
    size = po.calculate_size(1000, 0.85)
    assert size > 0
    assert size <= 100
    print("  [OK] profit_optimizer")


def test_adaptive_scanner():
    from alpha_system.config import CONFIG
    from alpha_system.market.adaptive_scanner import AdaptiveScanner
    sc = AdaptiveScanner(config=CONFIG)
    assert sc.can_scan() is True
    assert sc.get_interval() == CONFIG["SCAN_INTERVAL"]
    sc.record_scan(50)
    assert sc.current_interval == CONFIG["SCAN_INTERVAL"]
    sc.record_scan(0)
    assert sc.current_interval > CONFIG["SCAN_INTERVAL"]
    # Rate limit
    sc.report_rate_limit(30)
    assert sc.rate_limited is True
    sc.clear_rate_limit()
    assert sc.rate_limited is False
    print("  [OK] adaptive_scanner")


def test_logger():
    from alpha_system.utils.logger import setup_logger
    log = setup_logger("test_logger")
    log.info("test message")
    log.trade("test_market", "YES", 1, 0.1, 0.85)
    log.risk("test risk message")
    log.audit("TEST", "audit detail")
    print("  [OK] logger")


def run_all():

    print("=" * 50)
    print("  ALPHA SYSTEM — TEST SUITE")
    print("=" * 50)

    tests = [
        test_config,
        test_database,
        test_risk_engine,
        test_confidence_manager,
        test_cost_calculator,
        test_error_handler,
        test_kill_switch,
        test_profit_optimizer,
        test_adaptive_scanner,
        test_logger,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  [FAIL] {test.__name__}: {e}")

    print(f"\n  Results: {passed} passed, {failed} failed")
    print("=" * 50)

    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
