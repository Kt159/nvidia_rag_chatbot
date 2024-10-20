import { Client } from 'minio';
import { NextRequest, NextResponse } from 'next/server';

// Initialize MinIO client
const minioClient = new Client({
  endPoint: process.env.MINIO_ENDPOINT || 'localhost',
  port: 9000,
  useSSL: process.env.MINIO_USE_SSL === 'true',
  accessKey: process.env.MINIO_ACCESS_KEY!,
  secretKey: process.env.MINIO_SECRET_KEY!,
});

export const config = {
  api: {
    bodyParser: false,
  },
};

const bucketName: string = process.env.MINIO_BUCKET_NAME || 'default-bucket-name';

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const file = formData.get('file') as File;

    if (!file) {
      return NextResponse.json({ message: 'No file uploaded' }, { status: 400 });
    }

    const fileStream = file.stream();
    const fileBuffer = await file.arrayBuffer();
    const fileName = file.name;

    await minioClient.putObject(bucketName, fileName, Buffer.from(fileBuffer));

    return NextResponse.json({ message: 'File uploaded successfully' }, { status: 200 });
  } catch (error) {
    console.error('Error uploading file:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json({ message: 'MinIO upload error', error: errorMessage }, { status: 500 });
  }
}

export async function GET() {
  
  try {
    const objects = await minioClient.listObjects(bucketName, '', true);
    const documents: string[] = [];

    for await (const obj of objects) {
      documents.push(obj.name); // Push object name to documents array
    }

    return NextResponse.json(documents); // Return the list of document names as JSON
  } catch (error) {
    const err = error as Error;
    return NextResponse.json({ message: 'Error fetching documents', error: err.message }, { status: 500 });
  }
}

export async function DELETE(req: Request) {

  const { searchParams } = new URL(req.url);
  const documentId = searchParams.get('filename'); // Get the filename from the query parameters

  if (!documentId) {
    return NextResponse.json({ message: 'Filename is required' }, { status: 400 });
  }

  try {
    // Attempt to delete the object from MinIO
    await minioClient.removeObject(bucketName, documentId);
    return NextResponse.json({ message: 'Document deleted successfully' }, { status: 200 });
  } catch (error) {
    const err = error as Error;
    return NextResponse.json({ message: 'Error deleting document', error: err.message }, { status: 500 });
  }
}