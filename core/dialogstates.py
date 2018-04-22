from typing import Generator, List, NoReturn, Tuple, Union

from logzero import logger as log
from redis_collections import SyncableList

# Used to denote that a state will be used as fallback forever
INFINITE_LIFETIME = "infinite"


class _StateLifetime(object):
    """
    Internal data holding class to represent a state with its dynamic lifetime
    """

    def __init__(self, state: Union[Tuple, str], lifetime: int):
        self.state = state
        self.lifetime = lifetime

    def __str__(self):
        return f"{self.state} ({self.lifetime})"


class DialogStates(object):
    """
    Holds a priority queue of multiple states that a conversation may be in at the same time.
    Use the `put(new_state)` method to add a state to the queue with a specific lifetime, the latter being
    decremented by one for each call to `update_step()`.
    """

    def __init__(self, initial_state, redis=None, key=None):
        if redis:
            if not key:
                raise ValueError("If `redis` is used, then a `key` must be supplied.")
            self._states_queue = SyncableList(redis=redis, key=key)
        else:
            self._states_queue = []  # type: List[_StateLifetime]

        self.initial_state = initial_state
        self._init_states()

    def reset(self):
        self._states_queue.clear()
        self._init_states()
        if isinstance(self._states_queue, SyncableList):
            self._states_queue.sync()

    def _init_states(self):
        # There should always be a fallback state with infinite lifetime
        if not any(x.lifetime == INFINITE_LIFETIME for x in self._states_queue):
            self._states_queue.append(_StateLifetime(self.initial_state, INFINITE_LIFETIME))

    def put(self, new_state: Union[Tuple, str]):
        """
        Adds a new state to the priority queue of states for a given dialog.

        As tuples are hashable, they are a great choice for context sensitive dialog states.
        If the `new_state` argument is a tuple, then the last tuple value on the right will be treated as the
        lifetime of this state. The rest of the values will be condensed to a new tuple, or a single value if there
        is only one value left after stripping away the lifetime.

        If no integer value for the lifetime is given, an `INFINITE` lifetime is assumed.

        This mechanic serves convenience in that it simplifies returning states in the actual logic handlers:

        ```
        def do_something(response, context):
            response.say("Hello World!")

            # Return a tuple ("said", "hello world") as the new state with a lifetime of 3 cycles
            return ("said", "hello world", 3)
        ```

        """
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
        """
        Decrements all non-infinity state lifetimes in the internal queue and remove ones that have exceeded their
        lifetime.
        """
        to_remove = []
        for s in self._states_queue:
            current_lifetime = s.lifetime

            if current_lifetime == INFINITE_LIFETIME:
                continue

            new_lifetime = current_lifetime - 1

            if new_lifetime < 0:
                log.debug(f"State exceeded lifetime: {s}")
                to_remove.append(s)
            else:
                # Update to new lifetime
                s.lifetime = new_lifetime

        for s in to_remove:
            self._states_queue.remove(s)

        if isinstance(self._states_queue, SyncableList):
            self._states_queue.sync()

    def iter_states(self) -> Generator:
        # Returns a generator with the current states in order of recency
        return (s.state for s in self._states_queue)

    def __str__(self):
        states = "; ".join(str(x) for x in self._states_queue)
        return f"[{states}]"
