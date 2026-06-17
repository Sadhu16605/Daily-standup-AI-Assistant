import sys
from tabulate import tabulate
import standup_core as core


def show_report(report):

    print("\n" + "=" * 60)
    print("DAILY STANDUP REPORT")
    print("=" * 60)

    print("\nSummary:")
    print(report["summary"])

    print("\nBlockers:")
    if report["blockers"].empty:
        print("No blockers found.")
    else:
        print(
            tabulate(
                report["blockers"],
                headers="keys",
                tablefmt="grid",
                showindex=False
            )
        )

    print("\nPending Tasks:")
    if report["pending"].empty:
        print("No pending tasks.")
    else:
        print(
            tabulate(
                report["pending"],
                headers="keys",
                tablefmt="grid",
                showindex=False
            )
        )

    print("\nFollow-up Actions:")
    if report["followups"].empty:
        print("No follow-up actions required.")
    else:
        print(
            tabulate(
                report["followups"],
                headers="keys",
                tablefmt="grid",
                showindex=False
            )
        )

    print("\nRecommendations:")
    if report["recommendations"]:
        for number, recommendation in enumerate(
                report["recommendations"], start=1):
            print(f"{number}. {recommendation}")
    else:
        print("No recommendations available.")

    print("\nTeam Statistics")
    print("-" * 30)
    print("Total Members   :", report["total_members"])
    print("Total Blockers  :", report["total_blockers"])
    print("Total Followups :", report["total_followups"])


def main():

    if len(sys.argv) < 2:
        print("Usage: python standup_assistant.py standup.csv")
        return

    csv_file = sys.argv[1]

    try:
        data = core.load_standup_data(csv_file)
        report = core.build_report(data)
        show_report(report)

    except FileNotFoundError:
        print(f"Error: File '{csv_file}' not found.")

    except Exception as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()