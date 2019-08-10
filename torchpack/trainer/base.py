import time
import weakref

from tensorpack.utils.argtools import call_only_once
from tensorpack.utils.utils import humanize_time_delta

from torchpack.callbacks import Callback, Monitor, MonitorGroup, TimedCallbackGroup
from torchpack.trainer.exception import StopTraining
from torchpack.utils.logging import logger

__all__ = ['Trainer']

"""
The number of the currently ongoing epoch.

An epoch is defined to cover the moment before calling `before_epoch` until after calling `trigger_epoch`.
i.e., in the `trigger_epoch` of epoch 3, `self.epoch_num` is 3.
If you need use `self.trainer.epoch_num` in your callback, you'll need to know this.
"""
# return self.epoch_num

"""
The tensorflow global_step, i.e. how many times ``hooked_sess.run`` has been called.
"""
# return self.global_step

"""
The number of steps that have finished in the current epoch.
"""


# return self.local_step


class Trainer(object):
    """ Base class for a trainer.
    """

    is_chief = True
    """
    Whether this process is the chief worker in distributed training.
    Certain callbacks will only be run by chief worker.
    """

    def __init__(self, device='cuda'):
        self.device = device
        self.callbacks = None
        self.epoch_num = 0
        self.global_step = 0
        self.local_step = -1

    def register_callback(self, callback):
        """
        Register callbacks to the trainer.
        It can only be called before :meth:`Trainer.train()`.

        Args:
            callback (Callback or [Callback]): a callback or a list of callbacks

        Returns:
            succeed or not
        """
        if isinstance(callback, (list, tuple)):
            for x in callback:
                self.register_callback(x)
            return
        assert isinstance(callback, Callback), callback
        assert not isinstance(self.callbacks, TimedCallbackGroup), \
            'Cannot register more callbacks after trainer was setup!'
        if not self.is_chief and callback.chief_only:
            logger.warn('Callback {} is chief-only, skipped.'.format(str(callback)))
            return False
        else:
            self.callbacks.append(callback)
            return True

    def run_step(self, *args, **kwargs):
        """
        Defines what to do in one iteration.
        """
        raise NotImplementedError

    @call_only_once
    def setup_callbacks(self, callbacks, monitors):
        """
        Setup callbacks and monitors. Must be called after the main graph is built.

        Args:
            callbacks ([Callback]):
            monitors ([MonitorBase]):
        """
        assert isinstance(callbacks, list), callbacks
        assert isinstance(monitors, list), monitors

        self.callbacks = []
        for callback in callbacks:
            self.register_callback(callback)
        for callback in self.callbacks:
            assert not isinstance(callback, Monitor), 'Monitor cannot be pre-registered for now!'
        registered_monitors = []
        for m in monitors:
            if self.register_callback(m):
                registered_monitors.append(m)
        self.monitors = MonitorGroup(registered_monitors)
        self.register_callback(self.monitors)  # monitors is also a callback

        # some final operations that might modify the graph
        self.callbacks = TimedCallbackGroup(self.callbacks)
        self.callbacks.set_trainer(weakref.proxy(self))

    @call_only_once
    def main_loop(self, steps_per_epoch, starting_epoch, max_epoch):
        """
        Run the main training loop.

        Args:
            steps_per_epoch, starting_epoch, max_epoch (int):
        """

        self.starting_epoch = int(starting_epoch)
        self.max_epoch = int(max_epoch)
        self.steps_per_epoch = int(steps_per_epoch)

        # Allow empty epoch (no steps), if we want to run the callbacks only.
        assert self.steps_per_epoch >= 0 and self.max_epoch >= 0

        self.epoch_num = starting_epoch - 1
        self.global_step = self.epoch_num * self.steps_per_epoch

        try:
            self.callbacks.before_train()
            for self.epoch_num in range(self.starting_epoch, self.max_epoch + 1):
                logger.info('Training epoch {}/{} started.'.format(self.epoch_num, self.max_epoch))
                self.callbacks.before_epoch()
                start_time = time.time()

                self.model.train()
                # for self.local_step in range(self.steps_per_epoch):
                for self.local_step, (inputs, targets) in enumerate(self.loader):
                    # fixme
                    inputs = inputs.to(self.device, non_blocking=True)
                    targets = targets.to(self.device, non_blocking=True)
                    fd = dict(inputs=inputs, targets=targets)

                    self.callbacks.before_step()
                    self.run_step(fd)
                    self.callbacks.after_step()

                    self.callbacks.trigger_step()
                    self.global_step += 1

                self.callbacks.after_epoch()
                logger.info('Training epoch finished in {}.'.format(humanize_time_delta(time.time() - start_time)))
                self.callbacks.trigger_epoch()
            logger.info('Training has finished!')
        except StopTraining as e:
            logger.info('Training was stopped by exception {}.'.format(str(e)))
        except KeyboardInterrupt:
            logger.info('Detected Ctrl-C and exiting main loop.')
            raise
        finally:
            self.callbacks.after_train()

    def train(self, loader, model, criterion,
              callbacks=None, monitors=None,
              steps_per_epoch=None, starting_epoch=1, max_epoch=9999999):
        """
        Implemented by two lines:

        .. code-block:: python

            self.setup_callbacks(callbacks, monitors)
            self.main_loop(steps_per_epoch, starting_epoch, max_epoch)

        You can call those methods by yourself to have better control on details if needed.
        """
        self.loader = loader
        self.model = model
        self.criterion = criterion
        steps_per_epoch = len(self.loader)
        self.setup_callbacks(callbacks, monitors)
        self.main_loop(steps_per_epoch, starting_epoch, max_epoch)

    def state_dict(self):
        return dict(model=self.model.state_dict())

    def load_state_dict(self, state_dict):
        self.model.load_state_dict(state_dict['model'])

    def __new__(cls, *args, **kwargs):
        return super(Trainer, cls).__new__(cls)
