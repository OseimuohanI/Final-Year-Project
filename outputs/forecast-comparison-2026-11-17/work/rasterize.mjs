import sharp from 'sharp';
for (const source of process.argv.slice(2)) {
  await sharp(source,{density:260}).flatten({background:'#ffffff'}).png().toFile(source.replace(/\.svg$/,'.png'));
}
