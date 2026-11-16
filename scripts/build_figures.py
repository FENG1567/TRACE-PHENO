"""Build the nine figure sets from the bundled aggregate data."""
import argparse
import runpy
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'artifacts/figures')
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    scripts=ROOT/'figures/PublicationLayout'
    sys.path.insert(0,str(scripts))
    import layout_common
    layout_common.OUT=args.out.resolve()
    sys.argv=[str(scripts/'build_publication_figures.py'),'--all']
    runpy.run_path(str(scripts/'build_publication_figures.py'),run_name='__main__')
    print(f'Built nine figure sets; font={layout_common.FONT_FAMILY}; output={args.out}')
if __name__=='__main__':main()
