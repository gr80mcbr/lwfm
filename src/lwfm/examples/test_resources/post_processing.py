import argparse
from lwfm.base.Site import Site
from lwfm.base.SiteFileRef import FSFileRef
from pathlib import Path

def post_processing(output, destination):

    siteName = "local"

    site = Site.getSiteInstanceFactory(siteName)

    site.getAuthDriver().login()

    destRef = FSFileRef()

    destRef.setPath(destination)
    
    outputPath = Path(output)

    site.getRepoDriver().put(outputPath, destRef)

    print("Output has been downloaded.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Upload the output to the desired location.')
    parser.add_argument('--output', required=True, help='Path to the output')
    parser.add_argument('--destination', required=True, help='Path to the destination')

    args = parser.parse_args()

    post_processing(args.output, args.destination)
