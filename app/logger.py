"""
Comprehensive Logging System for Agadah Bot

Logs every run with:
- All inputs and outputs
- CrewAI agent logs
- Token usage (input/output)
- Model information for each call
- Timestamps and durations
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager


class RunLogger:
    """Logger for individual bot runs with detailed tracking."""

    def __init__(self, run_id: str, log_dir: str = "logs"):
        self.run_id = run_id
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Create run-specific log file
        self.log_file = self.log_dir / f"run_{run_id}.log"
        self.json_file = self.log_dir / f"run_{run_id}.json"

        # Initialize data structure
        self.run_data = {
            "run_id": run_id,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration_seconds": None,
            "user_input": None,
            "final_output": None,
            "agents": [],
            "total_tokens": {
                "input": 0,
                "output": 0,
                "total": 0
            },
            "models_used": [],
            "errors": []
        }

        # Set up file logger
        self.logger = logging.getLogger(f"run_{run_id}")
        self.logger.setLevel(logging.DEBUG)

        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        self.logger.info(f"Run {run_id} started")

    def log_input(self, user_input: str):
        """Log user input."""
        self.run_data["user_input"] = user_input
        self.logger.info(f"User input: {user_input}")

    def log_agent_start(self, agent_name: str, task_description: str):
        """Log when an agent starts."""
        agent_data = {
            "name": agent_name,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration_seconds": None,
            "task": task_description,
            "output": None,
            "tokens": {"input": 0, "output": 0},
            "model": None,
            "tool_calls": []
        }
        self.run_data["agents"].append(agent_data)
        self.logger.info(f"Agent '{agent_name}' started: {task_description}")
        return len(self.run_data["agents"]) - 1  # Return agent index

    def log_agent_end(self, agent_index: int, output: str):
        """Log when an agent completes."""
        if agent_index < len(self.run_data["agents"]):
            agent = self.run_data["agents"][agent_index]
            agent["end_time"] = datetime.now().isoformat()
            agent["output"] = output

            # Calculate duration
            start = datetime.fromisoformat(agent["start_time"])
            end = datetime.fromisoformat(agent["end_time"])
            agent["duration_seconds"] = (end - start).total_seconds()

            self.logger.info(
                f"Agent '{agent['name']}' completed in {agent['duration_seconds']:.2f}s"
            )
            self.logger.debug(f"Agent output: {output[:500]}...")

    def log_llm_call(
        self,
        agent_index: int,
        model: str,
        input_tokens: int,
        output_tokens: int,
        prompt: Optional[str] = None
    ):
        """Log LLM API call with token usage."""
        if agent_index < len(self.run_data["agents"]):
            agent = self.run_data["agents"][agent_index]
            agent["tokens"]["input"] += input_tokens
            agent["tokens"]["output"] += output_tokens
            agent["model"] = model

            # Update totals
            self.run_data["total_tokens"]["input"] += input_tokens
            self.run_data["total_tokens"]["output"] += output_tokens
            self.run_data["total_tokens"]["total"] += (input_tokens + output_tokens)

            # Track unique models
            if model not in self.run_data["models_used"]:
                self.run_data["models_used"].append(model)

            self.logger.info(
                f"LLM call - Model: {model}, "
                f"Input tokens: {input_tokens}, "
                f"Output tokens: {output_tokens}"
            )

            if prompt:
                self.logger.debug(f"Prompt: {prompt[:200]}...")

    def log_tool_call(self, agent_index: int, tool_name: str, result: str):
        """Log tool usage by agent."""
        if agent_index < len(self.run_data["agents"]):
            agent = self.run_data["agents"][agent_index]
            tool_data = {
                "name": tool_name,
                "timestamp": datetime.now().isoformat(),
                "result": result[:500] + "..." if len(result) > 500 else result
            }
            agent["tool_calls"].append(tool_data)

            self.logger.info(f"Tool used: {tool_name}")
            self.logger.debug(f"Tool result: {result[:200]}...")

    def log_error(self, error_msg: str, exception: Optional[Exception] = None):
        """Log error."""
        error_data = {
            "message": error_msg,
            "timestamp": datetime.now().isoformat(),
            "exception": str(exception) if exception else None
        }
        self.run_data["errors"].append(error_data)

        self.logger.error(error_msg)
        if exception:
            self.logger.exception(exception)

    def log_output(self, final_output: str):
        """Log final output."""
        self.run_data["final_output"] = final_output
        self.logger.info("Final output generated")
        self.logger.debug(f"Output: {final_output[:500]}...")

    def finalize(self):
        """Finalize the run and save JSON."""
        self.run_data["end_time"] = datetime.now().isoformat()

        # Calculate total duration
        start = datetime.fromisoformat(self.run_data["start_time"])
        end = datetime.fromisoformat(self.run_data["end_time"])
        self.run_data["duration_seconds"] = (end - start).total_seconds()

        # Save JSON
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(self.run_data, f, ensure_ascii=False, indent=2)

        # Summary log
        self.logger.info("=" * 60)
        self.logger.info("RUN SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Duration: {self.run_data['duration_seconds']:.2f}s")
        self.logger.info(f"Total tokens: {self.run_data['total_tokens']['total']}")
        self.logger.info(f"Input tokens: {self.run_data['total_tokens']['input']}")
        self.logger.info(f"Output tokens: {self.run_data['total_tokens']['output']}")
        self.logger.info(f"Models used: {', '.join(self.run_data['models_used'])}")
        self.logger.info(f"Agents executed: {len(self.run_data['agents'])}")
        self.logger.info(f"Errors: {len(self.run_data['errors'])}")
        self.logger.info("=" * 60)

        return self.run_data


# Global logger instance management
_current_logger: Optional[RunLogger] = None


def get_current_logger() -> Optional[RunLogger]:
    """Get the current run logger."""
    return _current_logger


def set_current_logger(logger: Optional[RunLogger]):
    """Set the current run logger."""
    global _current_logger
    _current_logger = logger


@contextmanager
def run_logger(user_input: str):
    """Context manager for run logging."""
    # Check if logging is enabled
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    enable_detailed_logs = os.getenv("ENABLE_DETAILED_LOGS", "true").lower() == "true"

    if not enable_detailed_logs:
        yield None
        return

    # Create run logger
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    logger = RunLogger(run_id)
    logger.log_input(user_input)

    # Set as current
    set_current_logger(logger)

    try:
        yield logger
    except Exception as e:
        logger.log_error("Run failed with exception", e)
        raise
    finally:
        # Finalize and clear
        logger.finalize()
        set_current_logger(None)
