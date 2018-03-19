from typing import Generator, List, NoReturn, Tuple, Union
from logzero import logger as log

INFINITE_LIFETIME = "infinite"


class _StateLifetime(object):
    def __init__(self, state: Union[Tuple, str], lifetime: int):
        self.state = state
        self.lifetime = lifetime

    def __str__(self):
        return f"{self.state} ({self.lifetime})"


class DialogStates(object):

    def __init__(self, initial_state):
        self._states_queue = [_StateLifetime(initial_state, INFINITE_LIFETIME)]  # type: List[_StateLifetime]

    def put(self, new_state: Union[Tuple, str]):
        if new_state is None:
            log.debug("No state change")
            return

        lifetime = INFINITE_LIFETIME

        if isinstance(new_state, tuple):
            try:
                # Interpret last tuple item as the new lifetime
                lifetime = int(new_state[-1])

                # Extract single item
                new_state = new_state[:-1]
                if len(new_state) == 1:
                    new_state = new_state[0]
            except ValueError:
                pass

        if lifetime is INFINITE_LIFETIME:
            # Clear stack since the lower items cannot be reached if new dialog_states has infinite lifetime
            self._states_queue.clear()
        else:
            if lifetime < 1:
                raise ValueError("State lifetime must be greater than or equal to 1.")

        state_container = _StateLifetime(new_state, lifetime)
        log.debug(f"New state added: {state_container}")
        self._states_queue.insert(0, state_container)

    def update_step(self) -> NoReturn:
        to_remove = []
        for s in self._states_queue:
            current_lifetime = s.lifetime

            if current_lifetime is INFINITE_LIFETIME:
                continue

            new_lifetime = current_lifetime - 1

            if new_lifetime < 0:
                to_remove.append(s)
            else:
                # Update to new lifetime
                s.lifetime = new_lifetime

        for s in to_remove:
            self._states_queue.remove(s)

    def iter_states(self) -> Generator:
        # Extract actual dialog_states without lifetime
        return (s.state for s in self._states_queue)

    def __str__(self):
        states = "; ".join(str(x) for x in self._states_queue)
        return f"[{states}]"
