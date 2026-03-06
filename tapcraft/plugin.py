"""Plugin base class for TapCraft custom actions."""


class TapPlugin:
    """Base class for TapCraft action plugins.

    To create a plugin:
    1. Create a .py file in the plugins/ directory
    2. Define a class that inherits from TapPlugin
    3. Set the 'name' class attribute (this is the action type in config.yaml)
    4. Implement the execute() method

    Example:
        from tapcraft.plugin import TapPlugin

        class MyAction(TapPlugin):
            name = "my-action"

            def execute(self, value: str, context: dict):
                print(f"My action triggered with value: {value}")
                print(f"Zone: {context['zone']}, Gesture: {context['gesture']}")
    """

    # The action type name used in config.yaml
    name: str = ""

    def execute(self, value: str, context: dict):
        """Execute the action.

        Args:
            value: The 'value' field from the config mapping.
            context: Dict containing:
                - zone: str — which zone was tapped
                - gesture: str — what gesture was detected
                - tap_count: int — number of taps in the gesture
                - fingers: int — number of fingers used
                - x: float — normalized x position (0-1)
                - y: float — normalized y position (0-1)
                - timestamp: float — time of last tap
        """
        raise NotImplementedError("Plugins must implement execute()")
