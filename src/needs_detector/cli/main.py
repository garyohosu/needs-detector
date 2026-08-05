import argparse
import sys
from pathlib import Path
from pydantic import ValidationError
from needs_detector.core.services import (ProjectService, DrawService, ExploreService, InterviewService,
    LearnService, ReportService, DoctorService, NextService, HumanGateError)
from needs_detector.domain.models.exceptions import MockFixtureNotFoundError, QuoteValidationError

def main():
    parser = argparse.ArgumentParser(prog='needs-detector')
    subparsers = parser.add_subparsers(dest='command')

    init_parser = subparsers.add_parser('init')
    init_parser.add_argument('name')
    init_parser.add_argument('--dir', default='.')

    idea_parser = subparsers.add_parser('add-idea')
    idea_parser.add_argument('file')

    source_parser = subparsers.add_parser('add-source')
    source_parser.add_argument('file')

    draw_parser = subparsers.add_parser('draw')
    draw_parser.add_argument('--provider', default='mock')
    draw_parser.add_argument('--fixture-key', default=None)

    explore_parser = subparsers.add_parser('explore')
    explore_parser.add_argument('--provider', default='mock')
    explore_parser.add_argument('--fixture-key', default=None)

    guide_parser = subparsers.add_parser('interview-guide')
    guide_parser.add_argument('--provider', default='mock')
    guide_parser.add_argument('--fixture-key', default=None)

    add_int_parser = subparsers.add_parser('add-interview')
    add_int_parser.add_argument('file')
    add_int_parser.add_argument('--data-classification', choices=['real', 'synthetic', 'unknown'], default='unknown')

    learn_parser = subparsers.add_parser('learn')
    learn_parser.add_argument('--provider', default='mock')
    learn_parser.add_argument('--fixture-key', default=None)

    report_parser = subparsers.add_parser('report')

    status_parser = subparsers.add_parser('status')
    
    import_parser = subparsers.add_parser('import-llm-response')
    import_parser.add_argument('file')

    doctor_parser = subparsers.add_parser('doctor')
    doctor_parser.add_argument('--json', action='store_true')

    next_parser = subparsers.add_parser('next')
    next_parser.add_argument('--json', action='store_true')

    args = parser.parse_args()

    # Pass the current working directory to services (assuming running in project dir unless init)
    project_dir = Path.cwd()

    try:
        if args.command == 'init':
            target_dir = Path(args.dir) / args.name
            ProjectService.init_project(target_dir, args.name)
            print(f"Initialized project {args.name} in {target_dir}")
        elif args.command == 'add-idea':
            ProjectService.add_idea(project_dir, args.file)
        elif args.command == 'add-source':
            ProjectService.add_source(project_dir, args.file)
        elif args.command == 'draw':
            DrawService.draw(project_dir, args.provider, args.fixture_key)
        elif args.command == 'explore':
            ExploreService.explore(project_dir, args.provider, args.fixture_key)
        elif args.command == 'interview-guide':
            InterviewService.generate_guide(project_dir, args.provider, args.fixture_key)
        elif args.command == 'add-interview':
            InterviewService.add_interview(project_dir, args.file, args.data_classification)
        elif args.command == 'learn':
            LearnService.learn(project_dir, args.provider, args.fixture_key)
        elif args.command == 'report':
            ReportService.generate_report(project_dir)
        elif args.command == 'status':
            ProjectService.status(project_dir)
        elif args.command == 'import-llm-response':
            from needs_detector.core.services import ImportService
            ImportService.import_response(project_dir, args.file)
        elif args.command == 'doctor':
            return DoctorService.run(project_dir, args.json)
        elif args.command == 'next':
            return NextService.run(project_dir, args.json)
        else:
            parser.print_help()
    except (ValueError, TypeError, OSError, ValidationError, HumanGateError,
            MockFixtureNotFoundError, QuoteValidationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
