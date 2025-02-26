import sys
from datetime import datetime
from glob import glob
import argparse

def analyze_log_gaps(log_files, context_lines=2, max_gap_seconds=30, ignore_lmdb=False):
    for log_file in log_files:
        print(f"\nAnalyzing {log_file} (looking for gaps > {max_gap_seconds} seconds):")
        if ignore_lmdb:
            print("Ignoring LMDB Mapsize increase events")
        
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            
        previous_time = None
        previous_line = None
        for i, line in enumerate(all_lines):
            # Skip empty lines
            if not line.strip():
                continue
                
            try:
                # Extract timestamp from start of line
                timestamp_str = line[:23]  # Get "YYYY-MM-DD HH:MM:SS.mmm"
                current_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                
                if previous_time:
                    gap = (current_time - previous_time).total_seconds()
                    if gap > max_gap_seconds:
                        # If ignoring LMDB and this is an LMDB line, skip it
                        if ignore_lmdb and "LMDB Mapsize increased" in line:
                            previous_time = current_time
                            previous_line = line
                            continue
                            
                        print("\nTime gap found:")
                        
                        # Print previous context lines
                        start_idx = max(0, i - context_lines - 1)
                        for context_line in all_lines[start_idx:i]:
                            print(context_line.strip())
                        
                        # Print gap visualization
                        gap_width = min(80, int(gap))  # Limit width to 80 chars
                        print("=" * gap_width + f" {gap:.1f} seconds ")
                        
                        # Print following context lines
                        end_idx = min(len(all_lines), i + context_lines + 1)
                        for context_line in all_lines[i:end_idx]:
                            print(context_line.strip())
                        
                previous_time = current_time
                previous_line = line
                
            except (ValueError, IndexError):
                continue  # Skip lines we can't parse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze time gaps in log files')
    parser.add_argument('pattern', help='file pattern (e.g., "logfile*" or "logs/*.log")')
    parser.add_argument('context_lines', nargs='?', type=int, default=2,
                      help='number of lines to show before and after each gap (default: 2)')
    parser.add_argument('min_gap_seconds', nargs='?', type=float, default=30,
                      help='minimum time gap to report in seconds (default: 30)')
    parser.add_argument('--ignore_LMDB', action='store_true',
                      help='ignore gaps caused by LMDB Mapsize increases')
    
    args = parser.parse_args()
    
    # Expand the pattern to get list of files
    log_files = glob(args.pattern)
    if not log_files:
        print(f"No files found matching pattern: {args.pattern}")
        sys.exit(1)
        
    analyze_log_gaps(log_files, args.context_lines, args.min_gap_seconds, args.ignore_LMDB)
