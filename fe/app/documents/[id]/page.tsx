import { DocumentReader } from "@/components/reader/document-reader";

export default async function DocumentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <DocumentReader documentId={id} />;
}
