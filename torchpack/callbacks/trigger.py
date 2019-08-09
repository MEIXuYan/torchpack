from .callback import Callback, ProxyCallback

__all__ = ['PeriodicTrigger', 'PeriodicCallback', 'EnableCallbackIf']


class PeriodicTrigger(ProxyCallback):
    """
    Trigger a callback every k global steps or every k epochs by its :meth:`trigger()` method.
    Most existing callbacks which do something every epoch are implemented
    with :meth:`trigger()` method. By default the :meth:`trigger()` method will be called every epoch.
    This wrapper can make the callback run at a different frequency.
    All other methods (``before/after_run``, ``trigger_step``, etc) of the given callback
    are unaffected. They will still be called as-is.
    """

    def __init__(self, callback, every_k_steps=None, every_k_epochs=None, before_train=False):
        """
        Args:
            callback (Callback): a Callback instance with a trigger method to be called.
            every_k_steps (int): trigger when ``global_step % k == 0``.
            every_k_epochs (int): trigger when ``epoch_num % k == 0``.
            before_train (bool): trigger in the :meth:`before_train` method.
        every_k_steps and every_k_epochs can be both set, but cannot be both None unless before_train is True.
        """
        assert isinstance(callback, Callback), type(callback)
        super().__init__(callback)
        if before_train is False:
            assert (every_k_epochs is not None) or (every_k_steps is not None), \
                "Arguments to PeriodicTrigger have disabled the triggerable!"
        self._step_k = every_k_steps
        self._epoch_k = every_k_epochs
        self._do_before_train = before_train

    def _before_train(self):
        self.callback.before_train()
        if self._do_before_train:
            self.callback.trigger()

    def _trigger_epoch(self):
        if self._epoch_k is None:
            return
        if self.trainer.epoch_num % self._epoch_k == 0:
            self.callback.trigger()

    def _trigger_step(self):
        self.callback.trigger_step()
        if self._step_k is None:
            return
        if self.trainer.global_step % self._step_k == 0:
            self.callback.trigger()

    def __str__(self):
        return 'PeriodicTrigger-' + str(self.callback)


class EnableCallbackIf(ProxyCallback):
    """
    Disable the ``{before,after}_epoch``, ``{before,after}_run``,
    ``trigger_{epoch,step}``
    methods of a callback, unless some condition satisfies.
    The other methods are unaffected.
    A more accurate name for this callback should be "DisableCallbackUnless", but that's too ugly.
    Note:
        If you use ``{before,after}_run``,
        ``pred`` will be evaluated only in ``before_run``.
    """

    def __init__(self, callback, predicate):
        """
        Args:
            callback (Callback):
            predicate (self -> bool): a callable predicate. Has to be a pure function.
                The callback is disabled unless this predicate returns True.
        """
        super().__init__(callback)
        self._predicate = predicate

    def _before_step(self, *args, **kwargs):
        if self._predicate(self):
            self._enabled = True
            return super()._before_step(*args, **kwargs)
        else:
            self._enabled = False

    def _after_step(self, ctx, rv):
        if self._enabled:
            super()._after_step(ctx, rv)

    def _before_epoch(self):
        if self._predicate(self):
            super()._before_epoch()

    def _after_epoch(self):
        if self._predicate(self):
            super()._after_epoch()

    def _trigger_epoch(self):
        if self._predicate(self):
            super()._trigger_epoch()

    def _trigger_step(self):
        if self._predicate(self):
            super()._trigger_step()

    def __str__(self):
        return "EnableCallbackIf-" + str(self.callback)


class PeriodicCallback(EnableCallbackIf):
    """
    The ``{before,after}_epoch``, ``{before,after}_run``, ``trigger_{epoch,step}``
    methods of the given callback will be enabled only when ``global_step % every_k_steps == 0`
    or ``epoch_num % every_k_epochs == 0``. The other methods are unaffected.
    Note that this can only makes a callback **less** frequent than itself.
    If you have a callback that by default runs every epoch by its :meth:`trigger()` method,
    use :class:`PeriodicTrigger` to schedule it more frequent than itself.
    """

    def __init__(self, callback, every_k_steps=None, every_k_epochs=None):
        """
        Args:
            callback (Callback): a Callback instance.
            every_k_steps (int): enable the callback when ``global_step % k == 0``.
            every_k_epochs (int): enable the callback when ``epoch_num % k == 0``.
                Also enable when the last step finishes (``epoch_num == max_epoch``
                and ``local_step == steps_per_epoch - 1``).
        every_k_steps and every_k_epochs can be both set, but cannot be both None.
        """
        assert isinstance(callback, Callback), type(callback)
        assert (every_k_epochs is not None) or (every_k_steps is not None), \
            'every_k_steps and every_k_epochs cannot both be None!'
        self._every_k_steps = every_k_steps
        self._every_k_epochs = every_k_epochs
        super(PeriodicCallback, self).__init__(callback, PeriodicCallback.predicate)

    def predicate(self):
        if self._every_k_steps is not None and self.trainer.global_step % self._every_k_steps == 0:
            return True
        if self._every_k_epochs is not None and self.trainer.epoch_num % self._every_k_epochs == 0:
            return True
        if self._every_k_epochs is not None:
            if self.trainer.local_step == self.trainer.steps_per_epoch - 1 and \
                    self.trainer.epoch_num == self.trainer.max_epoch:
                return True
        return False

    def __str__(self):
        return 'PeriodicCallback-' + str(self.callback)
