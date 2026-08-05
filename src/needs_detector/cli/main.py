import argparse
import sys
from pathlib import Path
from needs_detector.core.services import ProjectService, DrawService, ExploreService, InterviewService, LearnService, ReportService

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

    explore_parser = subparsers.add_parser('explore')
    explore_parser.add_argument('--provider', default='mock')

    guide_parser = subparsers.add_parser('interview-guide')

    add_int_parser = subparsers.add_parser('add-interview')
    add_int_parser.add_argument('file')

    learn_parser = subparsers.add_parser('learn')
    learn_parser.add_argument('--provider', default='mock')

    report_parser = subparsers.add_parser('report')

    status_parser = subparsers.add_parser('status')
    
    import_parser = subparsers.add_parser('import-llm-response')
    import_parser.add_argument('file')

    args = parser.parse_args()

    # Pass the current working directory to services (assuming running in project dir unless init)
    project_dir = Path.cwd()

    if args.command == 'init':
        target_dir = Path(args.dir) / args.name
        ProjectService.init_project(target_dir, args.name)
        print(f"Initialized project {args.name} in {target_dir}")
    elif args.command == 'add-idea':
        ProjectService.add_idea(project_dir, args.file)
    elif args.command == 'add-source':
        ProjectService.add_source(project_dir, args.file)
    elif args.command == 'draw':
        DrawService.draw(project_dir, args.provider)
    elif args.command == 'explore':
        ExploreService.explore(project_dir, args.provider)
    elif args.command == 'interview-guide':
        InterviewService.generate_guide(project_dir)
    elif args.command == 'add-interview':
        InterviewService.add_interview(project_dir, args.file)
    elif args.command == 'learn':
        LearnService.learn(project_dir, args.provider)
    elif args.command == 'report':
        ReportService.generate_report(project_dir)
    elif args.command == 'status':
        ProjectService.status(project_dir)
    elif args.command == 'import-llm-response':
        from needs_detector.core.services import ImportService
        ImportService.import_response(project_dir, args.file)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
