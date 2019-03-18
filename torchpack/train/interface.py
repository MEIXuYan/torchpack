def launch_train_with_config(config, trainer):
    """
    Train with a :class:`TrainConfig` and a :class:`Trainer`, to
    present the simple and old training interface. It basically does the following
    3 things (and you can easily do them by yourself if you need more control):
    1. Setup the input with automatic prefetching heuristics,
       from `config.data` or `config.dataflow`.
    2. Call `trainer.setup_graph` with the input as well as `config.model`.
    3. Call `trainer.train` with rest of the attributes of config.
    See the `related tutorial
    <https://tensorpack.readthedocs.io/tutorial/training-interface.html#with-modeldesc-and-trainconfig>`_
    to learn more.
    Args:
        config (TrainConfig):
        trainer (Trainer): an instance of :class:`SingleCostTrainer`.
    Example:
    .. code-block:: python
        launch_train_with_config(
            config, SyncMultiGPUTrainerParameterServer(8, ps_device='gpu'))
    """
    # assert isinstance(trainer, SingleCostTrainer), trainer
    # assert isinstance(config, TrainConfig), config
    assert config.model is not None
    assert config.dataflow is not None or config.data is not None

    model = config.model
    input = config.data or config.dataflow
    # input = apply_default_prefetch(input, trainer)

    # This is the only place where the `ModelDesc` abstraction is useful.
    # We should gradually stay away from this unuseful abstraction.
    # TowerFuncWrapper is a better abstraction (similar to tf.defun in the future)
    # trainer.setup_graph(
    #     model.train_step)
    trainer.setup_graph(
        input,
        model._build_graph_get_cost, model.get_optimizer)
    trainer.train(
        callbacks=config.callbacks,
        monitors=config.monitors,
        steps_per_epoch=config.steps_per_epoch,
        starting_epoch=config.starting_epoch,
        max_epoch=config.max_epoch,
        extra_callbacks=config.extra_callbacks)
