from .base_context import BaseContext


class JoinContext(BaseContext):
    def __init__(self, args, logger):
        super().__init__(args, logger)

        self.structured_params.update(
            {
                'raw_args': vars(args),
                'join_tasks': args.join_tasks,
                'reference_report': args.reference_report,
                'input_dir': args.input_dir,
                'report_name': args.report_name,
            }
        )
