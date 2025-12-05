/**
 * Download a file from a URL or generated object
 */
export const download = (
  urlOrGenerated: string | { url: string; type: string } | undefined,
  nodeId: string,
  extension: string
) => {
  if (!urlOrGenerated) {
    console.error('No content to download');
    return;
  }

  const url = typeof urlOrGenerated === 'string' ? urlOrGenerated : urlOrGenerated.url;
  const filename = `${nodeId}.${extension}`;

  // For data URLs (base64), we can download directly
  if (url.startsWith('data:')) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    return;
  }

  // For blob URLs or regular URLs, fetch and download
  fetch(url)
    .then(res => res.blob())
    .then(blob => {
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(blobUrl);
    })
    .catch(err => {
      console.error('Download failed:', err);
    });
};
