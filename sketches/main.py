import logging
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Actor:
    data: str = ""
    patterns: Dict[str, List[str]] = None
    
    def __post_init__(self):
        self.patterns = {}

class ActorSystem:
    def __init__(self):
        self.actors: Dict[str, Actor] = {}
        self.scope_stack: List[str] = []
        self.should_stop = False
        
    def get_or_create_actor(self, name: str) -> Actor:
        if name not in self.actors:
            self.actors[name] = Actor()
        return self.actors[name]
    
    def parse_patterns(self, code: str) -> Dict[str, List[str]]:
        patterns = {}
        for line in code.split('\n'):
            if "=>" in line:
                pattern, actions = line.split("=>", 1)
                pattern = pattern.strip()
                if pattern not in patterns:
                    patterns[pattern] = []
                patterns[pattern].extend(self._parse_actions(actions))
        return patterns
    
    def _parse_actions(self, actions: str) -> List[str]:
        return [action.strip() for action in actions.split(">") if action.strip()]
    
    def execute_scope(self, code: str, message: str = ""):
        if self.should_stop:
            raise TimeoutError("Execution timed out")
            
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        for line in lines:
            if self.should_stop:
                raise TimeoutError("Execution timed out")
                
            if "=>" in line:
                continue  # Skip pattern definitions during normal execution
            if ">" in line:
                parts = [p.strip() for p in line.split(">") if p.strip()]
                if len(parts) >= 2:
                    source, target = parts[-2:]
                    is_execute = target.startswith("@")
                    target_name = target[1:] if is_execute else target
                    
                    # Evaluate source if it's a quoted string
                    if source.startswith('"') and source.endswith('"'):
                        source = source[1:-1]
                    else:
                        source = self.get_or_create_actor(source).data
                    
                    if is_execute:
                        logger.debug(f"executing @{target_name} with ({source})")
                        self.execute_actor(target_name, source)
                    else:
                        logger.debug(f"{target_name} assigned with {repr(source)}")
                        target_actor = self.get_or_create_actor(target_name)
                        target_actor.data = source
                        if source.strip().startswith("{") and source.strip().endswith("}"):
                            target_actor.patterns = self.parse_patterns(source)
    
    def execute_actor(self, name: str, message: str = ""):
        if self.should_stop:
            raise TimeoutError("Execution timed out")
            
        actor = self.get_or_create_actor(name)
        
        if name == "print":
            print(message)
            return
            
        if actor.patterns:
            # Handle pattern matching
            for pattern, actions in actor.patterns.items():
                if pattern == message or not pattern:  # Empty pattern matches anything
                    for action in actions:
                        if action.startswith("@"):
                            self.execute_actor(action[1:], message)
                        else:
                            self.get_or_create_actor(action).data = message
                    return
        
        # If no patterns match but actor contains a scope, execute it
        if actor.data.strip().startswith("{") and actor.data.strip().endswith("}"):
            code = actor.data.strip()[1:-1]  # Remove { }
            self.execute_scope(code, message)

def run_with_timeout(system, timeout=1.0):
    def stop_system():
        system.should_stop = True
        
    timer = threading.Timer(timeout, stop_system)
    timer.start()
    try:
        logger.debug("program assigned with \"{.....}\"")
        system.get_or_create_actor("program").data = example_code[example_code.find("{"):example_code.rfind("}")+1]
        logger.debug("executing @program with no arguments")
        system.execute_actor("program")
    except TimeoutError:
        logger.debug("Program timed out after 1 second")
    finally:
        timer.cancel()

# Example code execution
example_code = r
"""
"{
    "hello world" > variable    # Write variable actor's contents to be a string
    variable > @print         # Execute: send variable's contents to print, this should print hello world

    "{
        "trigger" > var

        # Register match-cases for this block (assigned to 'loop')
        "trigger" => var > @loop            # When message "trigger" is received, send var to loop
                  => "loop" > @print        # OVERLOAD: also send "loop" to print when "trigger" matches
        "stop" => "stop" > var              # If message is "stop", assign "stop" to var

    }" > loop #write a string that contains executable code into loop actor

    "trigger" > @loop                # begin loop by sending it trigger.
}" > program

> @program                         # Step into the program scope with no arguments by sending it nothing

{
    any => "hello" > any #matches anything and assings "hello" to to it
} > function

variable > @function #variables contents become "hello"

"""

if __name__ == "__main__":
    system = ActorSystem()
    run_with_timeout(system)
